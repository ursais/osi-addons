# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One')
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two')

    @api.multi
    def _prepare_move_values(self):
        res = super()._prepare_move_values()
        res.update({
            'analytic_segment_one_id': self.analytic_segment_one_id.id,
            'analytic_segment_two_id': self.analytic_segment_two_id.id,
        })
        return res
