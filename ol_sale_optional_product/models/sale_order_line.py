# Import Odoo libs
from odoo import _, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """
    Adds a way to create optional products from sale line.
    """

    _inherit = "sale.order.line"

    # Methods #####
    def _get_values_to_add_to_optional(self):
        # Prepare a dictionary of values to add a product as an
        # optional line in the sale order.
        self.ensure_one()
        return {
            "order_id": self.order_id.id,
            "price_unit": self.price_unit,
            "name": self.name,
            "product_id": self.product_id.id,
            "quantity": self.product_uom_qty,
            "uom_id": self.product_uom.id,
            "mrp_bom_id": self.bom_id.id,
            "config_session_id": self.config_session_id.id,
            "line_id": self.id
        }

    def button_add_to_optional(self):
        # Button on sale order line that creates optional product
        self.add_option_to_optional()

    def add_option_to_optional(self):
        # Called from button method, adds the current product as an
        # optional line in the related sale order.
        self.ensure_one()

        sale_order = self.order_id

        # Check if the sale order can be edited on the portal; raise error if it cannot
        if not sale_order._can_be_edited_on_portal():
            raise UserError(_("You cannot add options to a confirmed order."))

        # Retrieve values for the optional line and create a new optional line in
        # the sale order
        values = self._get_values_to_add_to_optional()
        option_line = self.env["sale.order.option"].create(values)

        return option_line

    # END #########
