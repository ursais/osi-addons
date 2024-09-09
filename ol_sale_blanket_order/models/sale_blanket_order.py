# Import Odoo libs
import logging
from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleBlanketOrder(models.Model):
    """
    Add new fields to Sale blanket Order
    """

    _inherit = "sale.blanket.order"

    # COLUMNS #####

    auto_release = fields.Boolean(default=True, tracking=True)

    # END #########

    # METHODS #########

    def _prepare_so_line_vals(self, line):
        """Prepares the values for a sale order line based on the
        provided blanket order line."""
        return {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_uom": line.product_uom.id,
            "sequence": line.sequence,
            "price_unit": line.price_unit,
            "blanket_order_line": line.id,
            "product_uom_qty": line.remaining_uom_qty,
            "tax_id": [(6, 0, line.taxes_id.ids)],
            "customer_lead": line.customer_lead,
        }

    def _prepare_so_vals(
        self,
        customer,
        user_id,
        currency_id,
        pricelist_id,
        payment_term_id,
        order_lines_by_customer,
        original_request_date,
    ):
        # Prepares the values for creating a sale order based on the provided details.
        return {
            "partner_id": customer,
            "origin": self.name,
            "user_id": user_id,
            "currency_id": currency_id,
            "pricelist_id": pricelist_id,
            "payment_term_id": payment_term_id,
            "order_line": order_lines_by_customer[customer],
            "analytic_account_id": self.analytic_account_id.id,
            "original_request_date": original_request_date or fields.Date.today(),
        }

    @api.model
    def create_sale_order_cron(self):
        # Scheduled method to create sale orders automatically based on blanket orders.
        # Get the current date
        today = fields.Date.today()
        # Search for open blanket orders with auto_release enabled
        blanket_orders = self.search(
            [
                ("state", "=", "open"),
                ("auto_release", "=", True),
            ]
        )

        for order in blanket_orders:
            # Dictionary to store order lines by customer
            order_lines_by_customer = defaultdict(list)
            # Initialize variables to track order attributes
            currency_id = pricelist_id = user_id = payment_term_id = 0
            original_request_date = None

            for line in order.line_ids:
                # Check if the scheduled date plus customer lead time is due and
                # there is a remaining quantity to order
                if (
                    line.date_schedule
                    and (line.date_schedule - timedelta(days=line.customer_lead or 0.0))
                    <= today
                    and line.remaining_uom_qty > 0
                ):
                    # Check if product can be added to a quote, if not create activity
                    if not line.product_id.sale_ok:
                        order.activity_schedule(
                            "mail.mail_activity_data_warning",
                            note=_(
                                "Failed to create sale order. "
                                "Product %s is not allowed to be added to a sale order."
                                % line.product_id.display_name
                            ),
                            user_id=order.user_id.id or self.env.uid,
                        )
                        continue

                    # Prepare values for the sale order line
                    vals = self._prepare_so_line_vals(line)
                    # Group lines by customer
                    order_lines_by_customer[line.partner_id.id].append((0, 0, vals))

                    # Find smallest scheduled date
                    if (
                        original_request_date is None
                        or line.date_schedule < original_request_date
                    ):
                        original_request_date = line.date_schedule

                    # Track and validate the consistency of currency, pricelist, user,
                    # and payment terms across lines
                    if currency_id == 0:
                        currency_id = line.order_id.currency_id.id
                    elif currency_id != line.order_id.currency_id.id:
                        currency_id = False

                    if pricelist_id == 0:
                        pricelist_id = line.pricelist_id.id
                    elif pricelist_id != line.pricelist_id.id:
                        pricelist_id = False

                    if user_id == 0:
                        user_id = line.user_id.id
                    elif user_id != line.user_id.id:
                        user_id = False

                    if payment_term_id == 0:
                        payment_term_id = line.payment_term_id.id
                    elif payment_term_id != line.payment_term_id.id:
                        payment_term_id = False

            # If no order lines or inconsistent currency, skip to the next order
            if not order_lines_by_customer or not currency_id:
                continue

            # Create sale orders for each customer with valid order lines
            for customer in order_lines_by_customer:
                # Prepare values for the sale order
                order_vals = order._prepare_so_vals(
                    customer,
                    user_id,
                    currency_id,
                    pricelist_id,
                    payment_term_id,
                    order_lines_by_customer,
                    original_request_date,
                )
                sale_order = False
                try:
                    # Create the sale order
                    sale_order = self.env["sale.order"].create(order_vals)
                    # Log the creation of the sale order
                    _logger.info(
                        _(
                            f"Created sale order: {sale_order.id}, based on blanket order: {order.id}"
                        )
                    )
                except Exception as e:
                    order.activity_schedule(
                        "mail.mail_activity_data_warning",
                        note=_(f"Failed to create sale order. Reason is '{e}'"),
                        user_id=order.user_id.id or self.env.uid,
                    )

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
                        # Confirm the sale order
                        sale_order.action_confirm()
                    except Exception as e:
                        sale_order.activity_schedule(
                            "mail.mail_activity_data_warning",
                            note=_(
                                f"The sale order {sale_order.name} created from Blanket Order {order.name} couldn't be confirmed. \nReason: '{e}'"
                            ),
                            user_id=sale_order.user_id.id or self.env.uid,
                        )

    # END #########
