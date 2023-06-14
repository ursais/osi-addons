from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.stock_move_id and res.stock_move_id.product_id.type == 'consu' and res.stock_move_id.purchase_line_id:
            # convert stock move qty to purchase qty based on purchase line uom first
            qty = res.stock_move_id.product_id.uom_id._compute_quantity(res.quantity, res.stock_move_id.purchase_line_id.product_uom, round=False)
            # unit cost on stock move is based on purchase price
            res.unit_cost = res.stock_move_id.purchase_line_id.price_unit
            # cost is price x qty
            res.value = res.stock_move_id.purchase_line_id.price_unit * qty
        return res
