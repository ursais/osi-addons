# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        # Update Segments while Preparing PO Line
        data.update({'analytic_segment_one': line.analytic_segment_one.id,
                     'analytic_segment_two': line.analytic_segment_two.id})
        return data
