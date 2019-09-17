# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class PurchaseSubscription(models.Model):
    _inherit = 'purchase.subscription'

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False)
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False)

    @api.multi
    def _prepare_invoice_line(self, line, fiscal_position):
        res = super()._prepare_invoice_line(line, fiscal_position)
        res.update({
            'analytic_segment_one_id':
                self.order_id.analytic_segment_one_id.id,
            'analytic_segment_two_id':
                self.order_id.analytic_segment_two_id.id})
        return res


class PurchaseSubscriptionLine(models.Model):
    _inherit = 'purchase.subscription.line'

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False)
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False)
