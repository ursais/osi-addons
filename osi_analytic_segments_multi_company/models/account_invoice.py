# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # Mutli-Company (account_bill_line_distribution)
    def get_from_lines(self, from_lines, invoice_line_id,
                       invoice_id, amount, distribution, is_invoice):
        super().get_from_lines(from_lines, invoice_line_id,
                               invoice_id, amount, distribution, is_invoice)
        for line_id in from_lines:
            if line_id['inv_line'] == invoice_line_id.id:
                line_id['analytic_segment_one_id'] = invoice_line_id.\
                    analytic_segment_one_id.id
                line_id['analytic_segment_two_id'] = invoice_line_id.\
                    analytic_segment_two_id.id

    # Mutli-Company (account_bill_line_distribution)
    def get_to_lines(self, to_lines, line, company, invoice_id, is_invoice):
        super().get_to_lines(to_lines, line, company, invoice_id, is_invoice)
        for line_id in to_lines:
            invoice_line_id = self.env['account.invoice.line'].\
                browse(line_id['inv_line'])
            if invoice_line_id:
                line_id['analytic_segment_one_id'] = invoice_line_id.\
                    analytic_segment_one_id.id
                line_id['analytic_segment_two_id'] = invoice_line_id.\
                    analytic_segment_two_id.id
