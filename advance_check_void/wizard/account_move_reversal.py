# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    action_type = fields.Selection(
        [("void_check", "Void Check"), ("void_payment", "Void Check & Payment")],
        string="Action",
        default="void_check",
    )
    void_reason = fields.Char()

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        payment_check_void_obj = self.env["payment.check.void"]
        payment_check_history_obj = self.env["payment.check.history"]
        today_date = fields.Date.to_string(fields.Date.context_today(self))
        if self._context.get("is_void_button") and self._context.get("payment_id"):
            payment_id = self.env["account.payment"].browse(
                self._context.get("payment_id")
            )
            if payment_id.state in ("draft", "reversed"):
                raise ValidationError(
                    _("You can only reverse payments with status of posted or sent.")
                )
            if payment_id.reconciled_bill_ids == []:
                raise ValidationError(
                    _("You can only void checks and payments linked to invoices.")
                )

            payment_check_void_obj.create(
                {
                    "bill_ref": payment_id.ref,
                    "create_date": today_date,
                    "check_number": payment_id.check_number,
                    "state": "void",
                    "payment_id": payment_id.id,
                    "void_reason": self.void_reason,
                }
            )
            payment_id.write(
                {
                    "payment_state": "reversed",
                    "is_hide_check": True,
                    "void_reason": self.void_reason,
                }
            )
            domain = [
                ("payment_id", "=", payment_id.id),
                ("partner_id", "=", payment_id.partner_id.id),
                ("journal_id", "=", payment_id.journal_id.id),
            ]
            payment_check_history_ids = payment_check_history_obj.search(
                domain, order="id DESC", limit=1
            )
            payment_check_history_ids.write({"state": "void"})
        return res

    @api.model
    def fields_view_get(
        self, view_id=None, view_type=False, toolbar=False, submenu=False
    ):
        res = super(AccountMoveReversal, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        context = self._context
        pay_obj = self.env["account.payment"]
        if context.get("active_model") == "account.payment" and context.get(
            "active_ids"
        ):
            pay_ids = self._context.get("active_ids", False)
            for pay in pay_obj.browse(pay_ids):
                if pay.state in ("draft", "cancel"):
                    raise ValidationError(
                        _(
                            "State of payment is not posted or sent.\
                        Please select posted or sent payments only to reverse payment"
                        )
                    )
        return res

    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversal, self).default_get(fields)
        if self._context.get("is_void_button") and self._context.get("account_move_id"):
            move_id = self.env["account.move"].browse(
                self._context.get("account_move_id")
            )
            res["move_ids"] = move_id.ids
            res["refund_method"] = (
                (len(move_id) > 1 or move_id.move_type == "entry")
                and "cancel"
                or "refund"
            )
            res["residual"] = len(move_id) == 1 and move_id.amount_residual or 0
            res["currency_id"] = (
                len(move_id.currency_id) == 1 and move_id.currency_id.id or False
            )
            res["move_type"] = len(move_id) == 1 and move_id.move_type or False
        return res
