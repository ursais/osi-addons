# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help="The analytic account related to a sales order Line.",
        copy=False
    )

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        default_analytic_account = self.env[
            'account.analytic.default'].account_get(
                self.product_id.id, self.order_id.partner_id.id,
                self.order_id.user_id.id, fields.Date.today())
        if default_analytic_account:
            res.update({
                'account_analytic_id': default_analytic_account.analytic_id.id,
                'analytic_segment_one':
                    default_analytic_account.analytic_segment_one.id,
                'analytic_segment_two':
                    default_analytic_account.analytic_segment_two.id
            })
        return res

    @api.onchange('product_id')
    def _compute_analytic_acts(self):
        if self.product_id:
            rec = self.env['account.analytic.default'].account_get(
                self.product_id.id, self.order_id.partner_id.id, self.env.uid,
                fields.Date.today(), company_id=self.company_id.id)
            self.analytic_account_id = rec.analytic_id.id
            self.analytic_segment_one = rec.analytic_segment_one.id
            self.analytic_segment_two = rec.analytic_segment_two.id
        return
