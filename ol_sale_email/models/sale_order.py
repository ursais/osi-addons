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

    # Methods used in the exception definitions.
    def check_so_line_out_of_stock(self):
        show_exception = False
        # List to store product details for logging in the chatter
        products_out_of_stock = []

        # Iterate through each sale order line
        for line in self.order_line:
            # Check if:
            # 1. The product does not have a Bill of Materials (BoM)
            # 2. The requested quantity is greater than the available stock (virtual_available_at_date)
            # 3. The product is not make-to-order (is_mto is False)
            # 4. The product does not allow backorders (allow_backorder is False)
            if (
                not line.bom_id
                and line.product_uom_qty > line.virtual_available_at_date
                and not line.is_mto
                and not line.product_id.allow_backorder
            ):
                # Add the product name to the list of affected products
                products_out_of_stock.append(line.product_id.display_name)
                show_exception = True

        # If there are any products that failed the check, add a note in the chatter
        if products_out_of_stock:
            product_names = ", ".join(products_out_of_stock)
            message = f"The following SO line products are out of stock and cannot be backordered: {product_names}"
            self.message_post(body=message)

        # Return show_exception, failure (True) if any product is not available for backorder
        return show_exception

    def check_component_out_of_stock(self):
        show_exception = False
        # List to store product details for logging in the chatter
        products_out_of_stock = []

        # Iterate through each sale order line that has a Bill of Materials (BoM) and check its components.
        # For each BoM component (bom_line):
        # 1. The component is storable
        # 2. The required quantity of the component is greater than its available stock (virtual_available)
        # 3. The component does not allow backordering (allow_backorder is False)
        for line in self.order_line:
            if line.bom_id:
                # Check each BoM component that is stockable (type='product') for stock and backorder status
                for bom_line in line.bom_id.bom_line_ids:
                    if (
                        bom_line.product_id.type == "product"
                        and line.product_uom_qty * bom_line.product_qty
                        > bom_line.product_id.virtual_available
                        and not bom_line.product_id.allow_backorder
                    ):
                        # Add the product name to the list of failed components
                        products_out_of_stock.append(bom_line.product_id.display_name)
                        show_exception = True

        # If there are any stockable products that failed the check, add a note in the chatter
        if products_out_of_stock:
            product_names = ", ".join(products_out_of_stock)
            message = f"The following stockable BoM components are out of stock and cannot be backordered: {product_names}"
            self.message_post(body=message)

        # Return show_exception, failure (True) if any component is not available for backorder
        return show_exception

    # END #########
