from odoo import api, models
from odoo.tools import float_is_zero


class BlanketOrderLine(models.Model):
    _inherit = "sale.blanket.order.line"

    @api.onchange("product_id", "original_uom_qty")
    def onchange_product(self):
        res = super().onchange_product()
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        if self.product_id:
            if self.config_session_id:
                self.price_unit = (
                    self.config_session_id.price
                    or self.product_id.lst_price
                    or self._get_display_price()
                )
            if self.order_id.partner_id and float_is_zero(
                self.price_unit, precision_digits=precision
            ):
                self.price_unit = self._get_display_price() or self.product_id.lst_price
        return res
