# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def prepare_other_company_move_line_values(
            self, line, account=False, partner=False, keep=False):
        res = super().\
            prepare_other_company_move_line_values(line, account,
                                                   partner,
                                                   keep)
        if line.analytic_segment_one_id:
            res['analytic_segment_one_id'] = line.analytic_segment_one_id.id
        if line.analytic_segment_two_id:
            res['analytic_segment_two_id'] = line.analytic_segment_two_id.id
        return res

    def prepare_company_move_line_values(self, line, transfer_lines):
        super().prepare_company_move_line_values(line, transfer_lines)
        index = len(transfer_lines)
        if line.analytic_segment_one_id:
            transfer_lines[index-2][2]['analytic_segment_one_id'] = line.\
                analytic_segment_one_id.id
            transfer_lines[index-1][2]['analytic_segment_one_id'] = line.\
                analytic_segment_one_id.id
        if line.analytic_segment_two_id:
            transfer_lines[index-2][2]['analytic_segment_two_id'] = line.\
                analytic_segment_two_id.id
            transfer_lines[index-1][2]['analytic_segment_two_id'] = line.\
                analytic_segment_two_id.id
