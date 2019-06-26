# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    analytic_segment_one = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False
    )
    analytic_segment_two = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help="The analytic account related to a sales order Line.",
        copy=False
    )
    analytic_segment_one = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False
    )
    analytic_segment_two = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False
    )

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res.update(
            {'analytic_segment_one': self.analytic_segment_one.id or False,
             'analytic_segment_two':self.analytic_segment_two.id or False,
             'account_analytic_id': self.analytic_account_id.id or False,
            })
        return res
