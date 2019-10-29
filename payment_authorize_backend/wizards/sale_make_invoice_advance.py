# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        invoice = super(SaleAdvancePaymentInv, self)._create_invoice(
            order, so_line, amount)
        transactions = order.transaction_ids.filtered(
            lambda t: t.state != 'cancel' and not t.payment_id)
        invoice.write({
            'payment_method_id': order.payment_method_id.id,
            'payment_acquirer_id': order.payment_acquirer_id.id,
            'payment_token_id': order.payment_token_id.id,
            'payment_tx_id': transactions and transactions[0].id or order.payment_tx_id.id,
        })
        return invoice
