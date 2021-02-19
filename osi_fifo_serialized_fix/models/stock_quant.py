# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Extend method in stock_account/models/stock_quant.py
    # Change computed value for fifo stock.quant
    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_value(self):
        res = super()._compute_value()
        for quant in self:
            if quant.product_id.cost_method == 'fifo':
                svl_ids = self.env['stock.valuation.layer'].\
                    search([('product_id', '=', quant.product_id.id),
                            ('value', '>', 0)])
                for svl_id in svl_ids:
                    if quant.lot_id in svl_id.lot_ids:
                        if quant.product_id.tracking == 'lot':
                            quant.value = svl_id.value / svl_id.quantity \
                                * quant.inventory_quantity * -1
                        elif quant.product_id.tracking == 'serial':
                            quant.value = svl_id.value / svl_id.quantity \
                                * quant.inventory_quantity
        return res
