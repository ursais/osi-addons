# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models
from odoo.tools.misc import format_date


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def get_statement_entries(self):
        lines_ids_journal = []
        rl = []
        for stmt_line in self.line_ids:
            reconcile_ids = stmt_line.move_id.line_ids.full_reconcile_id
            if not stmt_line.move_id.line_ids.full_reconcile_id:
                rl.append(
                    {
                        "date": format_date(self.env, stmt_line.date),
                        "account_id": "      ",
                        "partner_id": stmt_line.partner_id.name,
                        "partner_bank_id": stmt_line.partner_bank_id,
                        "statement_id": stmt_line.name,
                        "move_id": "      ",
                        "ref": stmt_line.payment_ref,
                        "note": stmt_line.narration,
                        "matching_number": "      ",
                        "debit": stmt_line.amount > 0 and abs(stmt_line.amount) or 0.0,
                        "credit": stmt_line.amount < 0 and abs(stmt_line.amount) or 0.0,
                    }
                )
                continue
            else:
                suspense_line = self.env["account.move.line"].search(
                    [
                        ("full_reconcile_id", "=", reconcile_ids.id),
                        ("id", "not in", stmt_line.move_id.line_ids.ids),
                    ]
                )
                payment_line = suspense_line.move_id.line_ids.filtered(
                    lambda l: l.id != suspense_line.id
                    and l.account_id.internal_type in ("receivable", "payable")
                )

                for payment in payment_line:
                    rl.append(
                        {
                            "date": format_date(self.env, stmt_line.date),
                            "account_id": payment.account_id.code,
                            "partner_id": payment.partner_id.name,
                            "partner_bank_id": "      ",
                            "statement_id": stmt_line.name,
                            "move_id": payment.move_id.name,
                            "ref": payment.ref,
                            "note": "      ",
                            "matching_number": payment.full_reconcile_id.name,
                            "debit": stmt_line.amount > 0
                            and abs(stmt_line.amount)
                            or payment.debit,
                            "credit": stmt_line.amount < 0
                            and abs(stmt_line.amount)
                            or payment.credit,
                        }
                    )

                outstanding_line = suspense_line.move_id.line_ids.filtered(
                    lambda l: l.id not in (suspense_line + payment_line).ids
                    and l.account_id.internal_type not in ("receivable", "payable")
                )
                reconcile_ids = outstanding_line.full_reconcile_id

                if len(reconcile_ids) and len(outstanding_line):
                    partner_line = self.env["account.move.line"].search(
                        [
                            ("full_reconcile_id", "=", reconcile_ids.id),
                            ("id", "not in", outstanding_line.ids),
                        ]
                    )
                    payment_line = partner_line.move_id.line_ids.filtered(
                        lambda l: l.id != partner_line.id
                        and l.account_id.internal_type in ("receivable", "payable")
                    )

                    for payment in payment_line:
                        rl.append(
                            {
                                "date": format_date(self.env, stmt_line.date),
                                "account_id": payment.account_id.code,
                                "partner_id": payment.partner_id.name,
                                "partner_bank_id": "      ",
                                "statement_id": stmt_line.name,
                                "move_id": payment.move_id.name,
                                "ref": payment.ref,
                                "note": "      ",
                                "matching_number": payment.full_reconcile_id.name,
                                "debit": stmt_line.amount > 0
                                and abs(stmt_line.amount)
                                or payment.debit,
                                "credit": stmt_line.amount < 0
                                and abs(stmt_line.amount)
                                or payment.credit,
                            }
                        )
        return rl
