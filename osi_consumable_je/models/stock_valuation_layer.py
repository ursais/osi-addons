from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.stock_move_id and res.stock_move_id.product_id.type == 'consu' and res.stock_move_id.purchase_line_id:
            res.unit_cost = res.stock_move_id.purchase_line_id.price_unit
            res.value = res.stock_move_id.purchase_line_id.price_unit * res.quantity
        return res
