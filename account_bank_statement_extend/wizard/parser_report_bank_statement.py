# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class BankStatementReport(models.TransientModel):
    _name = "report.bank.statement"

    def _get_user_id(self):
        return self.env.uid

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")
    user_id = fields.Many2one("res.users", default=_get_user_id)

    def get_bank_statement_report(self):

        return self.env.ref(
            "account_bank_statement_extend.action_bank_statement_wiz_report"
        ).report_action(self)

    def get_starting_balance(self):
        bank_state_ids = self.env["account.bank.statement"].search([])
        starting_balance = 0.0
        for b_state in bank_state_ids:
            if b_state.date <= self.date_from:
                starting_balance += b_state.balance_start
        return starting_balance

    def get_ending_balance(self):
        bank_state_ids = self.env["account.bank.statement"].search([])
        ending_balance = 0.0
        for b_state in bank_state_ids:
            if b_state.date <= self.date_to:
                ending_balance += b_state.balance_end_real
        return ending_balance

    def get_bank_statement_report_data(self):
        bank_state_ids = self.env["account.bank.statement.line"].search(
            [("date", ">=", self.date_from), ("date", "<=", self.date_to)]
        )

        move_line_ids = [bank_state for bank_state in bank_state_ids]
        for b_state in bank_state_ids:
            for move_line in b_state.move_id.line_ids:
                if move_line.full_reconcile_id:
                    move_line = self.env["account.move.line"].search(
                        [("full_reconcile_id", "=", move_line.full_reconcile_id.id)]
                    )
                    for linein in move_line:
                        move_line_ids.append(linein)
        return move_line_ids

