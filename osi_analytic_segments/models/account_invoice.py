# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
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


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def invoice_line_move_line_get(self):
        res_temp = super(AccountInvoice, self).invoice_line_move_line_get()
        res = []
        invoice_line = self.env['account.invoice.line']

        for move_line_dict in res_temp:
            if move_line_dict['invl_id']:
                move_line_dict['analytic_segment_one'] = invoice_line.browse(
                    move_line_dict['invl_id']).analytic_segment_one.id
                move_line_dict['analytic_segment_two'] = invoice_line.browse(
                    move_line_dict['invl_id']).analytic_segment_two.id
            res.append(move_line_dict)

        return res

    @api.model
    def line_get_convert(self, line, part):

        res = super(AccountInvoice, self).line_get_convert(line,part)

        account_analytic_id = line.get('account_analytic_id', False)
        analytic_segment_one = line.get('analytic_segment_one',False)
        analytic_segment_two = line.get('analytic_segment_two', False)

        invl_id = line.get('invl_id', False)

        if invl_id:
            invoice_line = self.env['account.invoice.line'].browse(invl_id)                
            account_analytic_id = invoice_line.account_analytic_id.id
            analytic_segment_one = invoice_line.analytic_segment_one.id
            analytic_segment_two = invoice_line.analytic_segment_two.id

        res['account_analytic_id'] = account_analytic_id        
        res['analytic_segment_one']=analytic_segment_one
        res['analytic_segment_two']=analytic_segment_two

        return res
