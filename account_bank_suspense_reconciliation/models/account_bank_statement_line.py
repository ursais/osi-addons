# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    # replace core reconcile function to support reversal
    # of suspense line during reconcilation process
    def reconcile(self, lines_vals_list, to_check=False):
        """Perform a reconciliation on the current
        account.bank.statement.line with some counterpart
        account.move.line.

        If the statement line entry is not fully balanced after
        the reconciliation, an open balance will be created
        using the partner.

        :param lines_vals_list: A list of python dictionary containing:
            'id':           Optional id of an existing account.move.line.
                            For each line having an 'id', a new line will
                            be created in the current statement line.
            'balance':      Optional amount to consider during the
                            reconciliation. If a foreign currency is set on
                            the counterpart line in the same foreign currency
                            as the statement line, then this amount is
                            considered as the amount in foreign currency.
                            If not specified, the full balance is taken.
                            This value must be provided if 'id' is not.
            **kwargs:       Custom values to be set on the newly created
                            account.move.line.
        :param to_check:    Mark the current statement line as "to_check"
                            (see field for more details).
        """
        self.ensure_one()
        liquidity_lines, suspense_lines, other_lines = self._seek_for_lines()

        reconciliation_overview, open_balance_vals = self._prepare_reconciliation(
            lines_vals_list
        )

        # ==== Manage res.partner.bank ====

        if self.account_number and self.partner_id and not self.partner_bank_id:
            self.partner_bank_id = self._find_or_create_bank_account()

        # ==== Check open balance ====

        if open_balance_vals:
            if not open_balance_vals.get("partner_id"):
                raise UserError(
                    _(
                        "Unable to create an open balance for a statement line "
                        "/ without a partner set."
                    )
                )
            if not open_balance_vals.get("account_id"):
                raise UserError(
                    _(
                        "Unable to create an open balance for a statement line "
                        "/ because the receivable payable accounts are missing "
                        "/ on the partner."
                    )
                )

        # ==== Create & reconcile payments ====
        # When reconciling to a receivable/payable account, create an payment on the fly.

        pay_reconciliation_overview = [
            reconciliation_vals
            for reconciliation_vals in reconciliation_overview
            if reconciliation_vals.get("payment_vals")
        ]
        if pay_reconciliation_overview:
            payment_vals_list = [
                reconciliation_vals["payment_vals"]
                for reconciliation_vals in pay_reconciliation_overview
            ]
            payments = self.env["account.payment"].create(payment_vals_list)

            payments.action_post()

            for reconciliation_vals, payment in zip(
                pay_reconciliation_overview, payments
            ):
                reconciliation_vals["payment"] = payment

                # Reconcile the newly created payment with the counterpart line.
                (reconciliation_vals["counterpart_line"] + payment.line_ids).filtered(
                    lambda line: line.account_id
                    == reconciliation_vals["counterpart_line"].account_id
                ).reconcile()

        # ==== Create & reconcile lines on the bank statement line ====

        to_create_commands = [(0, 0, open_balance_vals)] if open_balance_vals else []

        # OSI - cannot delete journal item
        # to_delete_commands = [(2, line.id) for line in suspense_lines + other_lines]
        to_delete_commands = []

        # Cleanup previous lines.
        self.move_id.with_context(
            check_move_validity=False,
            skip_account_move_synchronization=True,
            force_delete=True,
        ).write(
            {
                "line_ids": to_delete_commands + to_create_commands,
                "to_check": to_check,
            }
        )

        # create a new JE to cancel suspense line and reconcile
        # suspense account / outstanding account
        suspense_vals_list = False
        if suspense_lines:
            suspense_vals_list = suspense_lines._prepare_move_line_vals()
            temp = suspense_vals_list["debit"]
            suspense_vals_list["debit"] = suspense_vals_list["credit"]
            suspense_vals_list["credit"] = temp
            suspense_vals_list["amount_currency"] = -suspense_vals_list[
                "amount_currency"
            ]
            accounts = self.journal_id.suspense_account_id

        # outstanding line
        line_vals_list = [
            reconciliation_vals["line_vals"]
            for reconciliation_vals in reconciliation_overview
        ]
        if suspense_vals_list and line_vals_list:
            del suspense_vals_list["move_id"]
            counterpart_lines = [[0, 0, suspense_vals_list]]
            for line_vals_line in line_vals_list:
                del line_vals_line["move_id"]
                counterpart_lines.append([0, 0, line_vals_line])
            move_vals = {
                "ref": "Posting statement line:" + self.name or "",
                "auto_post": True,
                "journal_id": self.journal_id.id,
                "move_type": "entry",
                "line_ids": counterpart_lines,
                "date": self.date,
            }

            # create new move that will reverse suspense account
            new_move = self.env["account.move"].create(move_vals)
            new_move.post()
            new_suspense_line = new_move.line_ids.filtered(
                lambda line: line.account_id in accounts
            )

            # reconcile suspense line to close out the statement line
            (suspense_lines + new_suspense_line).reconcile()
            accounts = (
                self.journal_id.payment_debit_account_id,
                self.journal_id.payment_credit_account_id,
            )
            new_lines = new_move.line_ids.filtered(
                lambda line: line.account_id in accounts
            )

            # get counterpart line on the stmt reconcile move
            if not len(new_lines):
                new_lines = new_move.line_ids - new_suspense_line
        else:
            new_lines = self.env["account.move.line"].create(line_vals_list)
            new_lines = new_lines.with_context(skip_account_move_synchronization=True)
        # OSI - end

        for reconciliation_vals, line in zip(reconciliation_overview, new_lines):
            if reconciliation_vals.get("payment"):
                accounts = (
                    self.journal_id.payment_debit_account_id,
                    self.journal_id.payment_credit_account_id,
                )
                counterpart_line = reconciliation_vals["payment"].line_ids.filtered(
                    lambda line: line.account_id in accounts
                )
            elif reconciliation_vals.get("counterpart_line"):
                counterpart_line = reconciliation_vals["counterpart_line"]
            else:
                continue

            (line + counterpart_line).reconcile()

        # Assign partner if needed (for example, when reconciling a statement
        # line with no partner, with an invoice; assign the partner of this invoice)
        if not self.partner_id:
            rec_overview_partners = {
                overview["counterpart_line"].partner_id.id
                for overview in reconciliation_overview
                if overview.get("counterpart_line")
                and overview["counterpart_line"].partner_id
            }
            if len(rec_overview_partners) == 1:
                self.line_ids.write({"partner_id": rec_overview_partners.pop()})

        # Refresh analytic lines.
        self.move_id.line_ids.analytic_line_ids.unlink()
        self.move_id.line_ids.create_analytic_lines()

    # replace core unreconcile function to support reversal of suspense line during
    # statement line revert reconciliation
    def button_undo_reconciliation(self):
        """Undo the reconciliation mades on the statement line and reset their journal items
        to their original states.
        """
        # OSI - begin
        # identify the reconciliations that need to be adjusted
        rec1 = self.line_ids.mapped("matched_debit_ids")
        rec2 = self.line_ids.mapped(
            "matched_debit_ids"
        ).debit_move_id.move_id.line_ids.mapped("matched_debit_ids")
        rec3 = self.line_ids.mapped("matched_credit_ids")
        rec4 = self.line_ids.mapped(
            "matched_credit_ids"
        ).debit_move_id.move_id.line_ids.mapped("matched_debit_ids")
        other_move = self.line_ids.mapped(
            "matched_debit_ids"
        ).debit_move_id.move_id.line_ids.mapped("move_id")

        # unreconcile the suspense lines and outstanding payment/receipt lines
        (rec1 + rec2 + rec3 + rec4).unlink()

        # cancel the suspense line journal created during reconcile process
        if len(other_move):
            other_move._reverse_moves(cancel=True)
        # OSI - end

        self.payment_ids.unlink()

        for st_line in self:
            st_line.with_context(force_delete=True).write(
                {
                    "to_check": False,
                    "line_ids": [(5, 0)]
                    + [
                        (0, 0, line_vals)
                        for line_vals in st_line._prepare_move_line_default_vals()
                    ],
                }
            )

    # core odoo method replaced for SOX compliance
    def unlink(self):
        # OVERRIDE to unlink the inherited account.move (move_id field) as well.
        moves = self.with_context(force_delete=True).mapped("move_id")
        res = super(models.Model, self).unlink()
        moves.write({"ref": "Statement line deleted"})
        moves.button_cancel()
        return res
