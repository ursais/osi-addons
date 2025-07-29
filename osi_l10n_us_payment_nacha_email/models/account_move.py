# Copyright 2025, AUTHOR(S)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def get_refund_detail(self):
        self.ensure_one()
        refund_move = []
        refund_amount = 0.0
        discount = 0.0
        bill_move = []
        for line in self.invoice_line_ids.filtered(lambda l: l.discount):
            subtotal = line.quantity * line.price_unit
            # discount += subtotal - line.price_subtotal
        if self.invoice_payments_widget:
            for data in self.invoice_payments_widget.get("content"):
                move_id = self.browse(data.get("move_id"))
                if move_id.move_type == "in_refund":
                    refund_move.append(move_id.name)
                    refund_amount += data.get("amount")

                if self.move_type == "in_refund" and move_id.move_type == "in_invoice":
                    bill_move.append(move_id.name)

        return [
            ",".join(refund_move) if refund_move else "",
            refund_amount,
            discount,
            ",".join(bill_move) if bill_move else "",
        ]
