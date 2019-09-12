# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False)
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False)
