# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        for rec in self:
            if rec.reversed_entry_id:
                payment_ids = self.env["account.payment"].search([("reversal_move_id", "=", rec.id)])
                for payment_id in payment_ids:
                    partial_reconciled_line_ids = self.env["account.partial.reconcile"].search(["|", ("id", "in", payment_id.reconciled_bill_ids.line_ids.matched_debit_ids.ids), ("id", "in", payment_id.reconciled_bill_ids.line_ids.matched_credit_ids.ids)])
                    for partial_id in partial_reconciled_line_ids:
                        account_move = (partial_id.debit_move_id or partial_id.credit_move_id).move_id
                        account_move.sudo().js_remove_outstanding_partial(partial_id.id)
        return super().action_post()
