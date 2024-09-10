# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SimpleVoidCheck(models.TransientModel):
    _name = "simple.void.check"
    _description = "Void Check"

    void_reason = fields.Char()
    payment_id = fields.Many2one("account.payment", string="Payment")

    def simple_void_check(self):
        """Void Check................."""
        payment_check_void_obj = self.env["payment.check.void"]
        check_hist_obj = self.env["payment.check.history"]
        account_move_obj = self.env["account.move"]
        payment_check_void_obj.create(
            {
                "bill_ref": self.payment_id.ref,
                "check_number": self.payment_id.check_number,
                "state": "void",
                "payment_id": self.payment_id.id,
                "void_reason": self.void_reason,
            }
        )
        self.payment_id.write({"is_visible_check": False})
        # Update payment check history..
        check_ids = check_hist_obj.search(
            [
                ("payment_id", "=", self.payment_id.id),
                ("check_number", "=", self.payment_id.check_number),
            ],
            order="id desc",
            limit=1,
        )
        if check_ids:
            check_ids.write({"state": "posted"})
        self.payment_id.action_unmark_sent()
        partial_reconciled_line_ids = self.env["account.partial.reconcile"].search(["|", ("id", "in", self.payment_id.reconciled_bill_ids.line_ids.matched_debit_ids.ids), ("id", "in", self.payment_id.reconciled_bill_ids.line_ids.matched_credit_ids.ids)])
        for partial_id in partial_reconciled_line_ids:
            account_move_obj.sudo().js_remove_outstanding_partial(partial_id.id)
