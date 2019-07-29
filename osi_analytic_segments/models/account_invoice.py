# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    analytic_segment_one_id = fields.Many2one(
        'analytic.segment.one',
        string='Analytic Segment One',
        copy=False)
    analytic_segment_two_id = fields.Many2one(
        'analytic.segment.two',
        string='Analytic Segment Two',
        copy=False)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def invoice_line_move_line_get(self):
        res_temp = super(AccountInvoice, self).invoice_line_move_line_get()
        res = []
        invoice_line = self.env['account.invoice.line']
        for move_line_dict in res_temp:
            if move_line_dict['invl_id']:
                move_line_dict['analytic_segment_one_id'] = invoice_line.\
                    browse(move_line_dict['invl_id']
                           ).analytic_segment_one_id.id
                move_line_dict['analytic_segment_two_id'] = invoice_line.\
                    browse(move_line_dict['invl_id']
                           ).analytic_segment_two_id.id
            res.append(move_line_dict)
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        account_analytic_id = line.get('account_analytic_id', False)
        analytic_segment_one = line.get('analytic_segment_one_id', False)
        analytic_segment_two = line.get('analytic_segment_two_id', False)
        invl_id = line.get('invl_id', False)
        if invl_id:
            invoice_line = self.env['account.invoice.line'].browse(invl_id)
            account_analytic_id = invoice_line.account_analytic_id.id
            analytic_segment_one = invoice_line.analytic_segment_one_id.id
            analytic_segment_two = invoice_line.analytic_segment_two_id.id
        res.update({'analytic_account_id': account_analytic_id,
                    'analytic_segment_one_id': analytic_segment_one,
                    'analytic_segment_two_id': analytic_segment_two})
        return res
