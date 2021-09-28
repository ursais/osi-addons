# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models
from odoo.tools.misc import format_date


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def get_base_reconcile_entries(self):
        lines_ids_journal = []
        for move_line in self.line_ids:
            rl = []
            for lines in move_line:
                lines = lines.move_id.line_ids
                if move_line.amount < 0.0:
                    if lines.full_reconcile_id:
                        move_line = self.env["account.move.line"].search(
                            [
                                ("full_reconcile_id", "=", lines.full_reconcile_id.id,),
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
                                        l.account_id.user_type_id.type
                                        in ["payable", "receivable"]
                                        and l.move_id.move_type
                                        in ["in_invoice", "out_invoice", "entry"]
                                        and len(rl) < 1
                                    ):
                                        bank_state_dict = self.get_bank_statement_lines_dict(
                                            l,
                                            l.account_id.user_type_id.type,
                                            lines_ids_journal,
                                            b_state,
                                        )
                                        if bank_state_dict:
                                            rl.append(bank_state_dict)
                                            lines_ids_journal.append(l.id)
                                        rl.append(
                                            {
                                                "date": format_date(self.env, l.date),
                                                "account_id": l.account_id.name,
                                                "partner_id": l.partner_id.name,
                                                "statement_id": self.name,
                                                "move_id": l.move_id.name,
                                                "ref": l.ref,
                                                "matching_number": l.full_reconcile_id.name,
                                                "debit": l.debit,
                                                "credit": l.credit,
                                            }
                                        )
                                    else:
                                        lines = l.move_id.line_ids._reconciled_lines()
                                        line_rec = self.env["account.move.line"].browse(
                                            lines
                                        )
                                        for line in line_rec:
                                            if (
                                                line.account_id.user_type_id.type
                                                in ["payable", "receivable",]
                                                and line.move_id.move_type
                                                in ["in_invoice", "out_invoice", "entry"]
                                                and len(rl) < 1
                                            ):
                                                rl.append(
                                                    {
                                                        "date": format_date(
                                                            self.env, l.date
                                                        ),
                                                        "account_id": line.account_id.name,
                                                        "partner_id": line.partner_id.name,
                                                        "statement_id": self.name,
                                                        "move_id": line.move_id.name,
                                                        "ref": line.ref,
                                                        "matching_number": line.full_reconcile_id.name,
                                                        "debit": line.debit,
                                                        "credit": line.credit,
                                                    }
                                                )
                else:
                    if lines.full_reconcile_id:
                        move_line = self.env["account.move.line"].search(
                            [
                                ("full_reconcile_id", "=", lines.full_reconcile_id.id,),
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
                                        l.account_id.user_type_id.type
                                        in ["payable", "receivable",]
                                        and l.move_id.move_type
                                        in ["in_invoice", "out_invoice", "entry"]
                                        and len(rl) < 1
                                    ):
                                        rl.append(
                                            {
                                                "date": format_date(self.env, l.date),
                                                "account_id": l.account_id.name,
                                                "partner_id": l.partner_id.name,
                                                "statement_id": self.name,
                                                "move_id": l.move_id.name,
                                                "ref": l.ref,
                                                "matching_number": l.full_reconcile_id.name,
                                                "debit": l.debit,
                                                "credit": l.credit,
                                            }
                                        )
                                    else:
                                        lines = l.move_id.line_ids._reconciled_lines()
                                        line_rec = self.env["account.move.line"].browse(
                                            lines
                                        )
                                        for line in line_rec:
                                            if (
                                                line.account_id.user_type_id.type
                                                in ["payable", "receivable",]
                                                and line.move_id.move_type
                                                in ["in_invoice", "out_invoice", "entry"]
                                                and len(rl) < 1
                                            ):
                                                rl.append(
                                                    {
                                                        "date": format_date(
                                                            self.env, l.date
                                                        ),
                                                        "account_id": line.account_id.name,
                                                        "partner_id": line.partner_id.name,
                                                        "statement_id": self.name,
                                                        "move_id": line.move_id.name,
                                                        "ref": line.ref,
                                                        "matching_number": line.full_reconcile_id.name,
                                                        "debit": line.debit,
                                                        "credit": line.credit,
                                                    }
                                                )
        return rl
