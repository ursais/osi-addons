# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare

from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    new_tx = fields.Boolean(
        string='New Transaction',
        default=True,
        copy=True,
    )
    commercial_partner_id = fields.Many2one(
        'res.partner',
        related='partner_id.commercial_partner_id',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        if self._context.get('website_order_tx', False) and vals.get('journal_id',False) and vals.get('payment_type', False):
            pay_journal = self.env['account.journal'].sudo().browse([vals['journal_id']])
            payment_type = vals['payment_type']
            if payment_type == 'inbound':
                payment_method = self.env.ref('account.account_payment_method_manual_in')
                if pay_journal.inbound_payment_method_ids:
                    payment_method = pay_journal.inbound_payment_method_ids[0]
            else:
                payment_method = self.env.ref('account.account_payment_method_manual_out')
                if pay_journal.outbound_payment_method_ids:
                    payment_method = pay_journal.outbound_payment_method_ids[0]
            vals['payment_method_id'] = payment_method.id
        return super(AccountPayment, self).create(vals)

    @api.onchange('new_tx')
    def onchange_new_tx(self):
        if self.new_tx:
            self.payment_transaction_id = False

    def _do_payment(self):
        """ Overwrite the existing base method from payment module """
        if self.payment_transaction_id.state in ('authorized', 'done'):
            return
        if not self.new_tx:
            if self.payment_transaction_id.id:
                return
            else:
                self.new_tx = True
        invoice_ids = self.invoice_ids.ids
        sale_ids = self.invoice_ids.mapped(
            'sale_ids').ids or self._context.get('sale_ids', [])
        if sale_ids:
            reference = "SO-%s" % (
                sale_ids and sale_ids[0],
            )
        elif invoice_ids:
            reference = "INV-%s" % (
                invoice_ids and invoice_ids[0],
            )
        else:
            reference = "PAY-%s" % (
                self.id,
            )
        reference = "%s-%s" % (
            reference,
            datetime.now().strftime('%H%M%S')
        )
        tx = self.env['payment.transaction'].sudo().create({
            'amount': self.amount,
            'acquirer_id': self.payment_token_id.acquirer_id.id,
            'type': 'server2server',
            'currency_id': self.currency_id.id,
            'reference': reference,
            'payment_token_id': self.payment_token_id.id,
            'partner_id': self.partner_id.id,
            'partner_country_id': self.partner_id.country_id.id,
            'invoice_id': invoice_ids and invoice_ids[0] or False,
            'sale_order_ids': [(6,0,sale_ids)] or False,
        })

        transaction = AuthorizeAPI(tx.acquirer_id)
        res = transaction.auth_and_capture(
            tx.payment_token_id, tx.amount, tx.reference)
        s2s_result = tx._authorize_s2s_validate_tree(res)

        if not s2s_result or tx.state != 'done':
            raise ValidationError(
                _("Payment transaction failed (%s)") %
                tx.state_message
            )

        self.payment_transaction_id = tx

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountPayment, self)._onchange_partner_id()
        if self.partner_id:
            # Removed the condition to check for auto_confirm != 'authorize'
            if 'domain' not in res:
                res['domain'] = {}
            res['domain'].update(
                {'payment_token_id': [
                    ('partner_id', 'child_of', self.partner_id.commercial_partner_id.id)]
                 }
            )
        return res

    @api.onchange('payment_method_id', 'journal_id')
    def _onchange_payment_method(self):
        if self.payment_method_code == 'electronic' and self.payment_token_id:
            # Skip if payment token is already selected in Invoice window
            return {}
        return super(AccountPayment, self)._onchange_set_payment_token_id()

    @api.multi
    def post(self):
        if 'default_journal_id' in self._context:
            context = dict(self._context or {})
            context.pop('default_journal_id', None)
            self = self.with_context(context)
        for payment in self:
            if (payment.payment_transaction_id.state == 'authorized'
                    and (payment.payment_transaction_id.acquirer_id.capture_manually
                    or payment.payment_transaction_id.acquirer_id.backend_confirm == 'authorize')) and not payment.new_tx:
                if payment.payment_transaction_id.payment_id:
                    raise UserError(
                        _('Selected Transaction is already linked to a payment'))
                company_currency = payment.journal_id.company_id.currency_id
                initial_tx_amt = payment.payment_transaction_id.amount
                if float_compare(
                        payment.payment_transaction_id.amount,
                        payment.amount,
                        precision_digits=company_currency.rounding) < 0:
                    raise UserError(
                        _('The Payment amount exceeds the selected Transaction amount!'))
                else:
                    invoice_ids = payment.invoice_ids.ids
                    payment.payment_transaction_id.write({
                        'invoice_id': invoice_ids and invoice_ids[0],
                        'amount': payment.amount,
                    })
                    payment.payment_transaction_id.action_capture()
                    if payment.payment_transaction_id.state != 'done':
                        raise ValidationError(_("Authorize.net error message: \n {0}".format(payment.payment_transaction_id.state_message)))
                    if initial_tx_amt != payment.amount and bool(self.env['ir.module.module'].sudo().search([('state','=','installed'), ('name','=','payment_authorize_partial_capture')]).ids):
                        payment.capture_post(initial_tx_amt)
            if payment.payment_transaction_id and payment.payment_transaction_id.payment_id.id != payment.id:
                payment.payment_transaction_id.payment_id = payment.id
            super(AccountPayment, payment).post()
            if payment.payment_type == 'inbound' and payment.payment_transaction_id and self._context.get('active_ids', []) and self._context.get('active_model','')=='account.invoice':
                self.env['account.invoice'].browse(self._context.get('active_ids', [])).write({
                    'payment_tx_id': payment.payment_transaction_id.id,
                    'payment_method_id': payment.journal_id.id,
                    'payment_token_id': payment.payment_token_id.id,
                })
