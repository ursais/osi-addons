# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        account_analytic_id = line.get('account_analytic_id', False)
        invl_id = line.get('invl_id', False)
        if invl_id:
            invoice_line = self.env['account.invoice.line'].browse(invl_id)
            account_analytic_id = invoice_line.account_analytic_id.id
        res['analytic_account_id'] = account_analytic_id
        return res

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        res_temp = super(AccountInvoice, self)._anglo_saxon_sale_move_lines(
            i_line)
        res = []
        for item in res_temp:
            item['invl_id'] = i_line.id
            res.append(item)
        return res
