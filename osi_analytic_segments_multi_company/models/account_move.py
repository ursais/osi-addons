# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Mutli-Company (account_bill_line_distribution)

    def get_from_lines(
        self, from_lines, invoice_line_id, invoice_id, amount, distribution, is_invoice
    ):
        super().get_from_lines(
            from_lines, invoice_line_id, invoice_id, amount, distribution, is_invoice
        )
        for line_id in from_lines:
            line_id[2][
                "analytic_segment_one_id"
            ] = invoice_line_id.analytic_segment_one_id.id
            line_id[2][
                "analytic_segment_two_id"
            ] = invoice_line_id.analytic_segment_two_id.id

    # Mutli-Company (account_bill_line_distribution)
    def get_to_lines(self, to_lines, line, company, invoice_id, is_invoice):
        super().get_to_lines(to_lines, line, company, invoice_id, is_invoice)
        for line_id in to_lines:
            line_id[2]["analytic_segment_one_id"] = line.get("analytic_segment_one_id")
            line_id[2]["analytic_segment_two_id"] = line.get("analytic_segment_two_id")
