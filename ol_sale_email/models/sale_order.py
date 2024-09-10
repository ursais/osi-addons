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
        Send backorder email if 'to_send_backorder_email' true
        Otherwise don't.
        """

        self.ensure_one()

        if not self.to_send_backorder_email:
            return False

        self.send_backorder_email()

        return True

    def get_backorder_products(self):
        """
        Get a list of storable products which are not currently available.
        """
        backorder_products = self.env["product.product"]

        # Collect all products from order lines and their BoM components
        product_ids = set()
        for line in self.order_line:
            if line.bom_id:
                product_ids.update(line.bom_id.bom_line_ids.mapped("product_id.id"))
            if line.product_id:
                product_ids.add(line.product_id.id)

        # Fetch the products in bulk to reduce database queries
        products = self.env["product.product"].browse(list(product_ids))

        # Filter products that are storable, allow backorders,
        # and are currently not available
        backorder_products = products.filtered(
            lambda p: p.type == "product" and p.allow_backorder and p.qty_available <= 0
        )

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
