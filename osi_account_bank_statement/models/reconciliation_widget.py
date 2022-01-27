# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def get_move_lines_for_bank_statement_line(self, st_line_id, partner_id=None, excluded_ids=None, search_str=False, offset=0, limit=None, mode=None):
        js_vals_list = super().get_move_lines_for_bank_statement_line(
            st_line_id=st_line_id,
            partner_id=partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            offset=offset,
            limit=limit,
            mode=mode
        )
        # Browse journal
        if self._context.get("journal_id", False):
            acc_ids = []
            acc_move_obj = self.env["account.move.line"]
            journal = self.env["account.journal"].browse(
                self._context.get("journal_id", False)
            )
            # Get journal's default outstanding payments account
            if journal.payment_credit_account_id:
                acc_ids.append(journal.payment_credit_account_id.id)
            # Get journal's default outstanding receipts account
            if journal.payment_debit_account_id:
                acc_ids.append(journal.payment_debit_account_id.id)
            expected_move_lines_ids = acc_move_obj.search(
                [("account_id", "in", acc_ids), ("statement_id", "=", False)]
            ).ids

        # filter out move lines and return only which fits in expected_move_lines_ids
        expected_move_lines_list = []
        for js_vals in js_vals_list:
            if js_vals['id'] in expected_move_lines_ids:
                expected_move_lines_list.append(js_vals)
        return expected_move_lines_list
