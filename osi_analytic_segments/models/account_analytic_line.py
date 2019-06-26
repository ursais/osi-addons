# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    analytic_segment_one = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One'
    )
    analytic_segment_two = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two'
    )
