# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    analytic_segment_one = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One'
    )
    analytic_segment_two = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two'
    )

    @api.one
    def _prepare_analytic_line(self):
        res = super(AccountMoveLine, self)._prepare_analytic_line()

        res[0]['analytic_segment_one'] = self.analytic_segment_one.id
        res[0]['analytic_segment_two'] = self.analytic_segment_two.id

        return res[0]
