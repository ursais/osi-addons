# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(
            line)
        # Update Segments while Preparing PO Line
        data.update(
            {'analytic_segment_one_id': line.analytic_segment_one_id.id,
             'analytic_segment_two_id': line.analytic_segment_two_id.id})
        return data
