# -*- coding: utf-8 -*-
from odoo import models, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_total_amount_using_same_currency(self, batch_result, early_payment_discount=True):
        self.ensure_one()
        amount = 0.0
        mode = False
        moves = batch_result['lines'].mapped('move_id')
        for move in moves:
            if early_payment_discount and move._is_eligible_for_early_payment_discount(move.currency_id, self.payment_date):
                amount += move.invoice_payment_term_id._get_amount_due_after_discount(move.amount_total, move.amount_tax)#todo currencies
                mode = 'early_payment'
            else:
                for aml in batch_result['lines'].filtered(lambda l: l.move_id.id == move.id):
                    amount += abs(aml.amount_residual_currency)
        return abs(amount), mode
