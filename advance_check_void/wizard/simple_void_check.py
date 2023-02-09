# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SimpleVoidCheck(models.TransientModel):
    _name = "simple.void.check"
    _description = "Void Check"

    void_reason = fields.Char(string="Void Reason")
    payment_id = fields.Many2one("account.payment", string="Payment")

    def simple_void_check(self):
        """Void Check................."""
        payment_check_void_obj = self.env["payment.check.void"]
        check_hist_obj = self.env["payment.check.history"]
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
        self.payment_id.action_unmark_sent()
        if check_ids:
            check_ids.write({"state": "void"})
        
