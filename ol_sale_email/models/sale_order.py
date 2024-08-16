# Import Python libs
import logging

# Import Odoo libs
from odoo import fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """
    Backorder email related functionality
    """

    _inherit = "sale.order"

    # COLUMNS #####

    to_send_backorder_email = fields.Boolean(
        string="Send backorder email", default=True, copy=False
    )

    # END #########

    # METHODS #########

    def toggle_backorder_email(self):
        """
        Toggle whether to send the email or not
        """
        for order in self:
            order.to_send_backorder_email = not order.to_send_backorder_email

    def send_backorder_email(self):
        """
        Send a email indicating which products are backordered and when they might be in stock
        """

        # Get a list of products which are not currently orderable
        backorder_products = self.get_backorder_products()

        if not backorder_products:
            # Continue only if there are backorder products
            # and the order is in a right state or is not confirmed by a Sales user
            return

        # Set up the context
        context = {
            "backordered_products": backorder_products.ids,
            "order_expected_date": self.expected_date,
        }
        local_context = self.env.context.copy()
        local_context.update(context)

        # Get the template and send the email
        template = self.env.ref("ol_sale_email.backorder_email_template")

        template.with_context(**local_context).send_mail(self.id)

        # Mark the Sale Order so we don't send this information again
        self.to_send_backorder_email = False

    def send_backorder_notification(self):
        """
        Handle backorder notifications
        1. Get backorder products if any
        2. Get order expected date
        3. ???
        4. Send email
        """

        self.ensure_one()

        if not self.to_send_backorder_email:
            return False

        self.send_backorder_email()

        return True

    def get_backorder_products(self):
        """
        Get a list of products which are not currently orderable
        """
        backorder_products = self.env["product.product"]
        for line in self.order_line:
            product_id = line.bom_id.bom_line_ids.product_id or False
            if (
                product_id
                and product_id.allow_backorder
                and product_id.qty_available <= 0
            ):
                backorder_products |= product_id
        return backorder_products

    def action_confirm(self):
        self.ensure_one()

        self.send_backorder_notification()

        # Handle Backorder Notification
        try:
            self.send_backorder_notification()
        except Exception as e:
            _logger.exception(
                f"Sending Backorder Notification failed for Order {self} reason: {e}"
            )
            self.message_post(
                message_type="notification",
                body=f"Backorder Notification failed: {str(e)}",
            )

        return super(SaleOrder, self).action_confirm()

    # END #########
