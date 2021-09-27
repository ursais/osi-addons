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
        bank_state_ids = self.env["account.bank.statement.line"].search([])
        starting_balance = 0.0
        for b_state in bank_state_ids:
            if b_state.date < self.date_from:
                starting_balance += b_state.amount
        return starting_balance

    def get_total_transection_amt(self):
        bank_state_ids = self.env["account.bank.statement.line"].search([])
        total_transection = 0.0
        for b_state in bank_state_ids:
            if b_state.date >= self.date_from and b_state.date <= self.date_from:
                total_transection += b_state.amount
        return total_transection

    def get_ending_balance(self):
        bank_state_ids = self.env["account.bank.statement.line"].search([])
        ending_balance = 0.0
        for b_state in bank_state_ids:
            if b_state.date <= self.date_to:
                ending_balance += b_state.amount
        return ending_balance

    def get_bank_statement_report_data(self):
        bank_state_ids = self.env["account.bank.statement.line"].search(
            [("date", ">=", self.date_from), ("date", "<=", self.date_to)]
        )
        rec_lines_dict = {}
        b_line_dict = []
        for b_state in bank_state_ids:
            rl = []
            rec_lines_dict = {
                "date": b_state.date,
                "account_id": None,
                "partner_id": b_state.partner_id.name,
                "statement_id": b_state.statement_id.name,
                "move_id": b_state.move_id.name,
                "ref": b_state.ref,
                "matching_number": None,
            }
            if b_state.amount >= 0.0:
                rec_lines_dict.update({"debit": b_state.amount, "credit": 0.0})
            else:
                rec_lines_dict.update({"debit": 0.0, "credit": b_state.amount})
            rl.append(rec_lines_dict)
            for move_line in b_state.move_id.line_ids:
                if b_state.amount < 0.0:
                    if move_line.full_reconcile_id:
                        move_line = self.env["account.move.line"].search(
                            [
                                (
                                    "full_reconcile_id",
                                    "=",
                                    move_line.full_reconcile_id.id,
                                ),
                                ("debit", "=", 0.0),
                            ]
                        )
                        for move in move_line:
                            move_line = self.env["account.move.line"].browse(
                                move_line._reconciled_lines()
                            )
                            for line in move_line:
                                lines = line.move_id.line_ids._reconciled_lines()
                                line_rec = self.env["account.move.line"].browse(lines)
                                for l in line_rec:
                                    if (
                                        l.move_id.move_type
                                        in ["in_invoice", "out_invoice"]
                                        and l.debit == 0.0
                                    ):
                                        rl.append(
                                            {
                                                "date": l.date,
                                                "account_id": l.account_id.name,
                                                "partner_id": l.partner_id.name,
                                                "statement_id": b_state.statement_id.name,
                                                "move_id": l.move_id.name,
                                                "ref": l.ref,
                                                "matching_number": l.full_reconcile_id.name,
                                                "debit": 0.0,
                                                "credit": l.credit,
                                            }
                                        )
                else:
                    if move_line.full_reconcile_id:
                        move_line = self.env["account.move.line"].search(
                            [
                                (
                                    "full_reconcile_id",
                                    "=",
                                    move_line.full_reconcile_id.id,
                                ),
                                ("debit", "!=", 0.0),
                            ]
                        )
                        for move in move_line:
                            move_line = self.env["account.move.line"].browse(
                                move_line._reconciled_lines()
                            )
                            for line in move_line:
                                lines = line.move_id.line_ids._reconciled_lines()
                                line_rec = self.env["account.move.line"].browse(lines)
                                for l in line_rec:
                                    if (
                                        l.move_id.move_type
                                        in ["in_invoice", "out_invoice"]
                                        and l.credit == 0.0
                                    ):
                                        rl.append(
                                            {
                                                "date": l.date,
                                                "account_id": l.account_id.name,
                                                "partner_id": l.partner_id.name,
                                                "statement_id": b_state.statement_id.name,
                                                "move_id": l.move_id.name,
                                                "ref": l.ref,
                                                "matching_number": l.full_reconcile_id.name,
                                                "debit": l.debit,
                                                "credit": 0.0,
                                            }
                                        )

            b_line_dict.append(rl)
        return b_line_dict
