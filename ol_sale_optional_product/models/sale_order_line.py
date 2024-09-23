# Import Odoo libs
from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    """
    Adds a way to create optional products from sale line.
    """

    _inherit = "sale.order.line"

    # Methods #####
    def _get_values_to_add_to_optional(self):
        self.ensure_one()
        return {
            "order_id": self.order_id.id,
            "price_unit": self.price_unit,
            "name": self.name,
            "product_id": self.product_id.id,
            "quantity": self.product_uom_qty,
            "uom_id": self.product_uom.id,
        }

    def button_add_to_optional(self):
        self.add_option_to_optional()

    def add_option_to_optional(self):
        self.ensure_one()

        sale_order = self.order_id

        if not sale_order._can_be_edited_on_portal():
            raise UserError(_("You cannot add options to a confirmed order."))

        values = self._get_values_to_add_to_optional()
        option_line = self.env["sale.order.option"].create(values)

        return option_line

    # END #########
