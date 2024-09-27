# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import float_is_zero


class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        super().onchange_product()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        if self.order_id.partner_id and float_is_zero(
            self.price_unit, precision_digits=precision
        ):
            # Use the custom logic for price_unit assignment
            self.price_unit = self._get_display_price() or self.product_id.lst_price
