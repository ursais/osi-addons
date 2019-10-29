# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    invoice_id = fields.Many2one(
        'account.invoice',
        'Invoice'
    )
    payment_id = fields.Many2one(
        'account.payment',
    )
    is_expired = fields.Boolean(compute="_compute_expiry_date",copy= False, help="Shows whether this payment transaction is expired after 30 days.")
    old_acquirer_reference = fields.Char(copy= False, help="Old transaction", readonly = True)
    creation_date = fields.Datetime(string="Transaction Creation Date", default=lambda self: fields.Datetime.now(), readonly = True)
    bk_order = fields.Boolean(string="Backend order", readonly= True)

    @api.multi
    def name_get(self):
        result = []
        state_dict = dict(self._fields['state'].selection)
        for tx in self:
            result.append(
                (tx.id, "%s - %s%s - %s" % (
                    tx.reference,
                    tx.currency_id.symbol,
                    tx.amount,
                    state_dict[tx.state],
                ))
            )
        return result

    @api.multi
    def _create_payment_transaction(self, vals):
        self = self.with_context(website_order_tx=True)
        tx = super(PaymentTransaction, self)._create_payment_transaction(vals)
        self.write({
            'payment_token_id': tx.payment_token_id and tx.payment_token_id.id or False,
            'payment_method_id': tx.acquirer_id and tx.acquirer_id.journal_id.id or False,
            'payment_tx_id' : tx.id or False,
            })
        return tx

    @api.depends()
    def _compute_expiry_date(self):
        for rec in self:
            rec.is_expired = False
            activity_deadline_date = fields.Datetime.from_string(rec.creation_date)
            current_date = fields.Datetime.from_string(fields.Datetime.now())
            delta = abs(current_date - activity_deadline_date)
            if delta.days > 30 and rec.acquirer_id.provider == 'authorize' and rec.state in 'authorized':
                transaction = AuthorizeAPI(rec.acquirer_id)
                auth_response = transaction.getTransactionDetailsResponse(rec.acquirer_reference)
                if auth_response == 'expired':
                    rec.is_expired = True

    @api.multi
    def re_authorize(self):
        if self.acquirer_id.provider == 'authorize' and self.is_expired and self.state in 'authorized':
            transaction = AuthorizeAPI(self.acquirer_id)
            auth_response = transaction.getTransactionDetailsResponse(self.acquirer_reference)
            _logger.info(_("This Transaction is {0}".format(auth_response)))
            if auth_response == 'expired':
                old_acq_ref = self.acquirer_reference
                res = transaction.authorize(self.payment_token_id, self.amount, self.reference)
                s2s_result = self._authorize_s2s_validate_tree(res)
                if not s2s_result:
                    raise ValidationError(_("Payment transaction failed {0}").format(self.state_message)
                                          )
                self.old_acquirer_reference = old_acq_ref
                self.sudo().write({'creation_date': fields.Datetime.now(),
                                   'acquirer_reference': res['x_trans_id']})

    @api.multi
    def _post_process_after_done(self):
        if self.bk_order == True:
            return
        return super(PaymentTransaction, self)._post_process_after_done()

class PaymentToken(models.Model):
    _inherit = 'payment.token'
    _rec_name = 'short_name'

    @api.multi
    def unlink(self):
        transactions = self.env['payment.transaction'].sudo().search(
            [('payment_token_id', 'in', self.ids)]
        )
        if transactions:
            self.sudo().write({
                'active': False,
            })
            return True
        else:
            return super(PaymentToken, self).unlink()


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    backend_confirm = fields.Selection([
        ('none', 'No Transaction'),
        ('authorize', 'Authorize Transaction'),
        ('authorize_capture', 'Authorize & capture Transaction')],
        string='Confirmation of Sales order',
        default='none',
        required=True,
    )



