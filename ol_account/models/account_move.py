# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from collections import defaultdict


class AccountMove(models.Model):
    """Inherit Account Move for field/method changes."""

    _inherit = "account.move"

    # COLUMNS #####

    payment_preference = fields.Many2one(
        comodel_name="res.paypref",
        string="Payment Preference",
        compute="_compute_payment_preference",
        tracking=True,
        store=True,
        help="Prefered Vendor payment method.",
    )
    sale_payment_method_id = fields.Many2one(
        comodel_name="payment.method",
        string="Customer Payment Method",
        help="Payment method selected coming from the sale order.",
    )
    invoice_due_date = fields.Date(
        compute="_compute_non_stored_invoice_date_due",
        help="Field with same date as due date, but to show just the date "
        "without the Remaining Days widget.",
    )

    # END #########
    # METHODS ######

    @api.depends(
        "company_id",
        "partner_id",
        "partner_id.payment_preference",
    )
    def _compute_payment_preference(self):
        # Group moves by company
        moves_by_company = defaultdict(lambda: self.env["account.move"])
        for move in self:
            moves_by_company[move.company_id] |= move

        # Compute payment preference per company context
        for company, moves in moves_by_company.items():
            moves_with_ctx = moves.with_company(company.id)
            for move in moves_with_ctx:
                move.payment_preference = move.partner_id.payment_preference

    def unlink(self):
        """
        Restrict deletion of account.move to only the system user
        and users with the special permission.
        Users should cancel account moves instead of deleting to adhere
        to Onlogic Accounting policy.
        """
        for move in self:
            # Allow deletion if the user is the system user to be safe
            # and not impact system operations
            if self.env.uid == 1:
                continue

            # Restrict deletion
            if not self.env.user.has_group("ol_account.group_account_move_delete"):
                raise UserError(
                    _(
                        "You are not allowed to delete account moves. "
                        "Please cancel them instead."
                    )
                )
            if move.state != "draft":
                raise UserError(
                    _(
                        "Only draft account moves can be deleted. "
                        "For posted moves, cancel them instead."
                    )
                )
        return super().unlink()

    def _auto_reconcile_deposits(self):
        """
        Automatically reconciles downpayment deposits with their corresponding invoices.
        - Filters invoices of type 'out_invoice'.
        - Identifies related sale orders.
        - Checks for unpaid downpayment invoices.
        - Matches and reconciles downpayment journal items with corresponding invoices.
        """
        for move in self.filtered(lambda m: m.move_type == "out_invoice"):
            so = self.env["sale.order"].search(
                [("invoice_ids", "in", [move.id])], limit=1
            )
            if not so:
                continue

            downpayment_moves = so.invoice_ids.filtered(
                lambda inv: inv.move_type == "out_invoice"
                and inv.payment_state != "paid"
                and inv.id != move.id
            )

            if not downpayment_moves:
                continue

            downpayment_lines = move.line_ids.filtered(lambda line: line.is_downpayment)

            for dp_move in downpayment_moves:
                dp_journal_items = dp_move.line_ids.filtered(
                    lambda line: line.is_downpayment and not line.reconciled
                )

                for dp_line in downpayment_lines:
                    matching_lines = dp_journal_items.filtered(
                        lambda line: line.balance == -dp_line.balance
                        and not line.reconciled
                    )

                    if matching_lines:
                        (matching_lines | dp_line).reconcile()

    def action_post(self):
        result = super().action_post()
        self._auto_reconcile_deposits()
        return result

    def action_invoice_print(self):
        """
        Override original invoice template
        """
        self.ensure_one()
        self.is_move_sent = True
        return self.env.ref("ol_account.action_generic_invoice_report").report_action(
            self
        )

    def get_report_invoice_data(self):
        data = {}
        for invoice in self:
            data[invoice.id] = {}
            order_data = False

            if invoice.line_ids.sale_line_ids:
                order_data = invoice.get_invoice_report_data_by_sale_order_lines()

            data[invoice.id]["sale_order"] = order_data

        return data

    def get_invoice_report_data_by_sale_order_lines(self):
        order_data = {
            "product_lines": [],
        }

        product_lines = self.env["sale.order.line"]

        for invoice_line in self.invoice_line_ids:
            for sale_order_line in invoice_line.sale_line_ids:
                if sale_order_line.is_delivery:
                    continue

                quote_config = sale_order_line.config_session_id or False
                product = sale_order_line.product_id
                template_attr_values = []
                product_lines |= sale_order_line

                if product and product.product_template_attribute_value_ids:
                    visible_values = (
                        product.product_template_attribute_value_ids.filtered(
                            lambda v: v.visible_to_user
                        ).sorted(key=lambda v: v.attribute_id.sequence)
                    )

                    # Prepare the configuration lines to match the structure you had before
                    template_attr_values = [
                        {
                            "attribute_id": v.attribute_id,
                            "attribute_name": v.attribute_id.name,
                            "value_name": v.product_attribute_value_id.product_id.name
                            or v.product_attribute_value_id.name,
                            "sequence": v.attribute_id.sequence,
                        }
                        for v in visible_values
                    ]

                order_line_data = {
                    "invoice_line": invoice_line,
                    "order_line": sale_order_line,
                    "quote_config": quote_config,
                    "quote_lines": template_attr_values,
                }

                order_data["product_lines"].append(order_line_data)

        # Set the shipping lines
        shipping_lines = self.mapped("invoice_line_ids.sale_line_ids").filtered(
            lambda l: l.is_delivery
        )

        order_data["shipping_lines"] = shipping_lines
        order_data["product_subtotal_amount"] = sum(
            product_lines.mapped("price_subtotal")
        )
        order_data["shipping_subtotal_amount"] = sum(
            shipping_lines.mapped("price_subtotal")
        )

        return order_data

    def get_invoice_report_data(self):
        for invoice in self:
            filtered_invoice = invoice
            filtered_invoice_data = {
                "sum_amount": invoice.amount_total,
                "out_invoice_amount": None,
                "out_refund_amount": None,
                "payment_received_amount": (
                    invoice.amount_total - invoice.amount_residual
                ),
                "residual_amount": invoice.amount_residual,
                "type": invoice.get_report_title(),
            }

        res = {"invoice": filtered_invoice, "invoice_data": filtered_invoice_data}

        return res

    def get_report_title(self):
        """Return the report title defined by marketing"""

        if self.move_type == "out_refund":
            return "Refund"

        return "Invoice"

    @api.depends("invoice_date_due")
    def _compute_non_stored_invoice_date_due(self):
        for move in self:
            move.invoice_due_date = move.invoice_date_due

    # END ##########
