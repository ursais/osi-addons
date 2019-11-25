# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One')
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two')

    @api.multi
    def _prepare_account_move_line(self, qty, cost,
                                   credit_account_id, debit_account_id):
        self.ensure_one()
        res = super(StockMove, self)._prepare_account_move_line(
            qty, cost, credit_account_id, debit_account_id)
        # Add analytic account in debit line
        if not self.analytic_account_id or not res:
            return res

        for num in range(0, 2):
            if res[num][2]["account_id"] != self.product_id.\
                    categ_id.property_stock_valuation_account_id.id:
                res[num][2].update({
                    'analytic_segment_one_id': self.analytic_segment_one_id.id,
                    'analytic_segment_two_id': self.analytic_segment_two_id.id,
                })
        return res
