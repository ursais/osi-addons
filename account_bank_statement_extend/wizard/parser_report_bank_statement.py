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
            if b_state.date >= self.date_from and b_state.date <= self.date_to:
                total_transection += b_state.amount
        return total_transection

    def get_ending_balance(self):
        bank_state_ids = self.env["account.bank.statement.line"].search([])
        ending_balance = 0.0
        for b_state in bank_state_ids:
            if b_state.date <= self.date_to:
                ending_balance += b_state.amount
        return ending_balance

    def get_bank_statement_dict(self, l, account_type, lines, b_state):
        if l.id not in lines and account_type in ["payable", "receivable"]:
            return {
                "date": l.date,
                "account_id": l.account_id.name,
                "partner_id": l.partner_id.name,
                "statement_id": b_state.statement_id.name,
                "move_id": l.move_id.name,
                "ref": l.ref,
                "matching_number": l.full_reconcile_id.name,
                "debit": l.debit,
                "credit": l.credit,
            }
        return None

    def get_bank_statement_report_data(self):
        bank_state_ids = self.env["account.bank.statement.line"].search(
            [("date", ">=", self.date_from), ("date", "<=", self.date_to)]
        )
        rec_lines_dict = {}
        b_line_dict = []
        lines_ids_journal = []
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
                                    if l.account_id.user_type_id.type in [
                                        "payable",
                                        "receivable",
                                    ] and l.move_id.move_type in [
                                        "in_invoice",
                                        "out_invoice",
                                    ]:
                                        bank_state_dict = self.get_bank_statement_dict(
                                            l,
                                            l.account_id.user_type_id.type,
                                            lines_ids_journal,
                                            b_state,
                                        )
                                        if bank_state_dict:
                                            rl.append(bank_state_dict)
                                            lines_ids_journal.append(l.id)
                                    else:
                                        lines = l.move_id.line_ids._reconciled_lines()
                                        line_rec = self.env["account.move.line"].browse(
                                            lines
                                        )
                                        for line_move in line_rec:
                                            if line_move.account_id.user_type_id.type in [
                                                "payable",
                                                "receivable",
                                            ] and line_move.move_id.move_type in [
                                                "in_invoice",
                                                "out_invoice",
                                            ]:
                                                bank_state_dict = self.get_bank_statement_dict(
                                                    line_move,
                                                    line_move.account_id.user_type_id.type,
                                                    lines_ids_journal,
                                                    b_state,
                                                )
                                                if bank_state_dict:
                                                    rl.append(bank_state_dict)
                                                    lines_ids_journal.append(
                                                        line_move.id
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
                                    if l.account_id.user_type_id.type in [
                                        "payable",
                                        "receivable",
                                    ] and l.move_id.move_type in [
                                        "in_invoice",
                                        "out_invoice",
                                    ]:
                                        bank_state_dict = self.get_bank_statement_dict(
                                            l,
                                            l.account_id.user_type_id.type,
                                            lines_ids_journal,
                                            b_state,
                                        )
                                        if bank_state_dict:
                                            rl.append(bank_state_dict)
                                            lines_ids_journal.append(l.id)
                                    else:
                                        lines = l.move_id.line_ids._reconciled_lines()
                                        line_rec = self.env["account.move.line"].browse(
                                            lines
                                        )
                                        for line_move in line_rec:
                                            if line_move.account_id.user_type_id.type in [
                                                "payable",
                                                "receivable",
                                            ] and line_move.move_id.move_type in [
                                                "in_invoice",
                                                "out_invoice",
                                            ]:
                                                bank_state_dict = self.get_bank_statement_dict(
                                                    line_move,
                                                    line_move.account_id.user_type_id.type,
                                                    lines_ids_journal,
                                                    b_state,
                                                )
                                                if bank_state_dict:
                                                    rl.append(bank_state_dict)
                                                    lines_ids_journal.append(
                                                        line_move.id
                                                    )
            b_line_dict.append(rl)
        return b_line_dict
