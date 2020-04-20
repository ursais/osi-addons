# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ReasonCode(models.Model):
    _inherit = "reason.code"

    def _get_default_segment_one(self):
        return self.env["analytic.segment.one"].get_default_segment_one()

    analytic_account_id = fields.Many2one(
        string='Analytic Account',
        comodel_name='account.analytic.account')
    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        default=_get_default_segment_one)
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two')
