# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountAnalyticDefault(models.Model):
    _inherit = "account.analytic.default"

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False)
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False)


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        rec = self.env['account.analytic.default'].account_get(
            self.product_id.id, self.invoice_id.partner_id.id, self.env.uid,
            fields.Date.today(), company_id=self.company_id.id)
        self.analytic_segment_one_id = rec.analytic_segment_one_id.id
        self.analytic_segment_two_id = rec.analytic_segment_one_id.id
        return res

    def _set_additional_fields(self, invoice):
        rec = self.env['account.analytic.default'].account_get(
            self.product_id.id, self.invoice_id.partner_id.id,
            self.env.uid,
            fields.Date.today(), company_id=self.company_id.id)
        if rec and not self.analytic_segment_one_id:
            self.analytic_segment_one_id = rec.analytic_segment_one_id.id
        if rec and not self.analytic_segment_two_id:
            self.analytic_segment_two_id = rec.analytic_segment_two_id.id
        super(AccountInvoiceLine, self)._set_additional_fields(invoice)
