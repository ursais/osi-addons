# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAnalyticDefault(models.Model):
    _inherit = "account.analytic.default"

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


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        rec = self.env['account.analytic.default'].account_get(
            self.product_id.id, self.invoice_id.partner_id.id, self.env.uid,
            fields.Date.today(), company_id=self.company_id.id)
        self.analytic_segment_one = rec.analytic_segment_one.id
        self.analytic_segment_two = rec.analytic_segment_one.id
        return res

    def _set_additional_fields(self, invoice):
        if not self.analytic_segment_one:
            rec = self.env['account.analytic.default'].account_get(
                self.product_id.id, self.invoice_id.partner_id.id,
                self.env.uid,
                fields.Date.today(), company_id=self.company_id.id)
            if rec:
                self.analytic_segment_one = rec.analytic_segment_one.id
        if not self.analytic_segment_two:
            rec = self.env['account.analytic.default'].account_get(
                self.product_id.id, self.invoice_id.partner_id.id,
                self.env.uid,
                fields.Date.today(), company_id=self.company_id.id)
            if rec:
                self.analytic_segment_two = rec.analytic_segment_two.id

        super(AccountInvoiceLine, self)._set_additional_fields(invoice)
