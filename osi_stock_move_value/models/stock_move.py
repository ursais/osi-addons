# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from odoo.addons import decimal_precision as dp


class StockMove(models.Model):
    _inherit = "stock.move"

    stock_value = fields.Float(
        "Stock Value",
        compute="_compute_stock_value",
        digits=dp.get_precision("Product Unit of Measure"),
    )

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            product_id = val.get("product_id", False)
            if product_id:
                qty = val.get("qty_done") or val.get("product_uom_qty") or 0
                product = self.env["product.product"].browse(product_id)
                cost_method = product.product_tmpl_id.categ_id
                if product.cost_method not in ("fifo"):
                    val["price_unit"] = product.standard_price
                    val["stock_value"] = product.standard_price * qty

        res = super(StockMove, self).create(vals_list)
        return res

    @api.depends("price_unit", "product_uom_qty")
    def _compute_stock_value(self):
        for move in self:
            price = move.price_unit or move.product_id.standard_price
            move.stock_value = price * move.product_uom_qty
