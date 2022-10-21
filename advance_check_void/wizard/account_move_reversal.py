# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    void_reason = fields.Char(string="Void Reason")

    def reverse_moves(self):
        payment_check_void_obj = self.env["payment.check.void"]
        payment_check_history_obj = self.env["payment.check.history"]
        today_date = fields.Date.to_string(fields.Date.context_today(self))
        if self._context.get("is_void_button") and self._context.get("payment_id"):
            payment_id = self.env["account.payment"].browse(
                self._context.get("payment_id")
            )
            if payment_id.state != "sent":
                raise ValidationError(
                    _("You can only reverse payments with status of sent.")
                )
            if payment_id.reconciled_invoice_ids == []:
                raise ValidationError(
                    _("You can only void checks and payments linked to invoices.")
                )
            payment_check_void_obj.create(
                {
                    "bill_ref": payment_id.payment_reference,
                    "create_date": today_date,
                    "check_number": payment_id.check_number,
                    "state": "void",
                    "payment_id": payment_id.id,
                    "void_reason": self.void_reason,
                }
            )
            payment_id.write(
                {
                    "state": "cancelled",
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
            ac_move_id = payment_id.move_line_ids[0]
            res = (
                self.env["account.move"]
                .browse(ac_move_id.move_id.id)
                .reverse_moves(self.date, self.journal_id or False)
            )
            if res:
                return {
                    "name": _("Reverse Moves"),
                    "type": "ir.actions.act_window",
                    "view_type": "form",
                    "view_mode": "tree,form",
                    "res_model": "account.move",
                    "domain": [("id", "in", res)],
                }
        ac_move_ids = self._context.get("active_ids", False)
        res = (
            self.env["account.move"]
            .browse(ac_move_ids)
            .reverse_moves(self.date, self.journal_id or False)
        )
        if res:
            return {
                "name": _("Reverse Moves"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "account.move",
                "domain": [("id", "in", res)],
            }
        return {"type": "ir.actions.act_window_close"}

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
