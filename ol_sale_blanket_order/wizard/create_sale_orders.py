# Import Odoo libs
from collections import defaultdict

from odoo import _, models
from odoo.exceptions import UserError, ValidationError


class BlanketOrderWizard(models.TransientModel):
    """
    Override Blanket Order create order wizard to add
    invoice/delivery addresses.
    """

    _inherit = "sale.blanket.order.wizard"

    # METHODS #########

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
        partner_invoice_id,
        partner_shipping_id,
        contact_ids,
    ):
        date_schedule = min(self.line_ids.mapped("date_schedule"))
        return {
            "partner_id": customer,
            "origin": self.blanket_order_id.name,
            "user_id": user_id,
            "currency_id": currency_id,
            "pricelist_id": pricelist_id,
            "payment_term_id": payment_term_id,
            "order_line": order_lines_by_customer[customer],
            "analytic_account_id": self.blanket_order_id.analytic_account_id.id,
            "partner_invoice_id": partner_invoice_id,
            "partner_shipping_id": partner_shipping_id,
            "original_request_date": date_schedule,
            "contact_ids": contact_ids,
            "ignore_exception": True,
            "account_manager_id": self.blanket_order_id.account_manager_id.id,
        }

    def create_sale_order(self):
        order_lines_by_customer = defaultdict(list)
        currency_id = 0
        pricelist_id = 0
        user_id = 0
        payment_term_id = 0
        partner_invoice_id = 0
        partner_shipping_id = 0
        contact_ids = 0
        for line in self.line_ids.filtered(lambda line: line.qty != 0.0):
            if line.qty > line.remaining_uom_qty:
                raise UserError(_("You can't order more than the remaining quantities"))
            vals = self._prepare_so_line_vals(line)
            order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

            if currency_id == 0:
                currency_id = line.blanket_line_id.order_id.currency_id.id
            elif currency_id != line.blanket_line_id.order_id.currency_id.id:
                currency_id = False

            if partner_invoice_id == 0:
                partner_invoice_id = line.blanket_line_id.order_id.partner_invoice_id.id
            elif (
                partner_invoice_id
                != line.blanket_line_id.order_id.partner_invoice_id.id
            ):
                partner_invoice_id = False

            if partner_shipping_id == 0:
                partner_shipping_id = (
                    line.blanket_line_id.order_id.partner_shipping_id.id
                )
            elif contact_ids != line.blanket_line_id.order_id.partner_shipping_id.id:
                partner_shipping_id = False

            if contact_ids == 0:
                contact_ids = line.blanket_line_id.order_id.contact_ids.ids
            elif contact_ids != line.blanket_line_id.order_id.contact_ids.ids:
                contact_ids = False

            if pricelist_id == 0:
                pricelist_id = line.blanket_line_id.pricelist_id.id
            elif pricelist_id != line.blanket_line_id.pricelist_id.id:
                pricelist_id = False

            if user_id == 0:
                user_id = line.blanket_line_id.user_id.id
            elif user_id != line.blanket_line_id.user_id.id:
                user_id = False

            if payment_term_id == 0:
                payment_term_id = line.blanket_line_id.payment_term_id.id
            elif payment_term_id != line.blanket_line_id.payment_term_id.id:
                payment_term_id = False

        if not order_lines_by_customer:
            raise UserError(_("An order can't be empty"))

        if not currency_id:
            raise UserError(
                _(
                    "Can not create Sale Order from Blanket "
                    "Order lines with different currencies"
                )
            )

        res = []
        for customer in order_lines_by_customer:
            order_vals = self._prepare_so_vals(
                customer,
                user_id,
                currency_id,
                pricelist_id,
                payment_term_id,
                order_lines_by_customer,
                partner_invoice_id,
                partner_shipping_id,
                contact_ids,
            )
            sale_order = self.env["sale.order"].create(order_vals)
            if sale_order:
                try:
                    # Check to make sure all products are able to be sold
                    # raise confirmation error if not which will create an activity.
                    if any(
                        not line.product_id.sale_ok_confirm
                        or not line.product_id.ship_ok
                        for line in sale_order.order_line
                    ):
                        raise ValidationError(
                            "A Product's state is preventing order confirmation."
                        )

                    # Confirm the sale order - ignore_exception is True so
                    # exceptions won't trigger
                    sale_order.action_confirm()

                    # Remove Ignore Exceptions which will also trigger exception check
                    sale_order.write({"ignore_exception": False})
                except Exception as e:
                    sale_order.activity_schedule(
                        "mail.mail_activity_data_warning",
                        note=_(
                            f"The sale order {sale_order.name} created from Blanket Order {sale_order.name} couldn't be confirmed. \nReason: '{e}'"
                        ),
                        user_id=sale_order.user_id.id or self.env.uid,
                    )
            res.append(sale_order.id)

        # Compute remaining amounts on bo lines so bookings trigger
        sale_order.order_line.blanket_order_line._compute_remaining_prices()

        return {
            "domain": [("id", "in", res)],
            "name": _("Sales Orders"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "context": {"from_sale_order": True},
            "type": "ir.actions.act_window",
        }

    # END #########
