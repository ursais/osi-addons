# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.addons.payment_authorize.models.authorize_request import AuthorizeAPI
from odoo.addons.sale.models.payment import PaymentTransaction


def _reconcile_after_transaction_done(self):
    # Override of '_set_transaction_done' in the 'payment' module
    # to confirm the quotations automatically and to generate the invoices if needed.
    sales_orders = self.mapped('sale_order_ids').filtered(lambda so: so.state in ('draft', 'sent'))
    for so in sales_orders:
        # For loop because some override of action_confirm are ensure_one.
        so.with_context(send_email=True, website_order_tx=True).action_confirm()
    # invoice the sale orders if needed
    self._invoice_sale_orders()
    res = super(PaymentTransaction, self)._reconcile_after_transaction_done()
    if self.env['ir.config_parameter'].sudo().get_param('sale.automatic_invoice'):
        default_template = self.env['ir.config_parameter'].sudo().get_param('sale.default_email_template')
        if default_template:
            ctx_company = {'company_id': self.acquirer_id.company_id.id,
                           'force_company': self.acquirer_id.company_id.id,
                           'mark_invoice_as_sent': True,
                           }
            for trans in self.filtered(lambda t: t.sale_order_ids):
                trans = trans.with_context(ctx_company)
                for invoice in trans.invoice_ids:
                    invoice.message_post_with_template(int(default_template), notif_layout="mail.mail_notification_paynow")
    return res
PaymentTransaction._reconcile_after_transaction_done = _reconcile_after_transaction_done


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transaction_ids = fields.One2many(
        'payment.transaction',
        'sale_order_ids',
        copy=False,
    )
    payment_token_id = fields.Many2one(
        'payment.token',
        string="Saved payment token",
        help='Lists the Payment Tokens available',
        copy=False,
    )
    is_electronic_payment_method = fields.Boolean(
        'Is Electronic Payment Method?',
        related='payment_method_id.is_electronic_payment_method',
    )
    commercial_partner_id = fields.Many2one(
        'res.partner',
        related='partner_id.commercial_partner_id',
        readonly=True,
    )
    commercial_partner_invoice_id = fields.Many2one(
        'res.partner',
        related='partner_invoice_id.commercial_partner_id',
        readonly=True,
    )
    hide_create_transaction = fields.Boolean(
        compute='compute_hide_create_transaction',
    )
    hide_addcard = fields.Boolean(
        compute='_compute_hide_addcard'
    )
    payment_acquirer_id = fields.Many2one('payment.acquirer', string='Payment Acquirer', copy=False)
    payment_tx_id = fields.Many2one('payment.transaction', string='Last Transaction', copy=False, readonly= True)
    payment_transaction_count = fields.Integer(string="Number of payment transactions",compute='_compute_payment_transaction_count')

    @api.one
    @api.depends('transaction_ids')
    def _compute_payment_transaction_count(self):
        for order in self:
            order.payment_transaction_count = len(order.transaction_ids)

    def action_view_transaction(self):
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Payment Transactions',
            'res_model': 'payment.transaction',
        }
        if self.payment_transaction_count == 1:
            action.update({
                'res_id': self.transaction_ids.id,
                'view_mode': 'form',
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.transaction_ids.ids)],
            })
        return action

    @api.multi
    @api.depends('payment_method_id')
    def _compute_hide_addcard(self):
        authorize_journals = self.env['account.journal'].sudo().search(
            [('payment_acquirer_id.provider', '=', 'authorize')])
        for sale in self:
            sale.hide_addcard = True
            if sale.payment_method_id.id in authorize_journals.ids:
                sale.hide_addcard = False

    @api.depends('state', 'payment_acquirer_id')
    def compute_hide_create_transaction(self):
        for sale in self:
            auto_transaction_flag = sale.payment_acquirer_id.backend_confirm != 'none'
            hide_create_transaction = False
            if sale.state == 'done':
                hide_create_transaction = True
            else:
                if not auto_transaction_flag:
                    hide_create_transaction = True
                elif sale.payment_transaction_count > 0:
                    pass
                elif auto_transaction_flag: # and sale.payment_transaction_count == 0:
                    hide_create_transaction = True
            sale.hide_create_transaction = hide_create_transaction

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        transactions = self.transaction_ids.filtered(
            lambda t: t.state != 'cancel' and not t.payment_id)
        invoice_vals.update({
            'payment_method_id': self.payment_method_id.id,
            'payment_acquirer_id': self.payment_acquirer_id.id,
            'payment_token_id': self.payment_token_id.id,
            'payment_tx_id': transactions and transactions[0].id or self.payment_tx_id.id,
        })
        return invoice_vals

    @api.onchange('payment_method_id')
    def onchange_payment_method_id(self):
        for order in self:
            if order.payment_method_id.is_electronic_payment_method:
                if order.payment_method_id.payment_acquirer_id:
                    order.payment_acquirer_id = order.payment_method_id.payment_acquirer_id.id
                else:
                    raise UserError(
                        _('The Payment Acquirer is not selected in the Payment Method!'))
            else:
                order.payment_acquirer_id = False

    @api.onchange('payment_acquirer_id', 'partner_invoice_id')
    def onchange_payment_acquirer_id(self):
        for order in self:
            payment_token_id = False
            if order.payment_acquirer_id:
                payment_token_id = self.env['payment.token'].search(
                    [('partner_id', 'child_of', order.commercial_partner_invoice_id.id),
                     ('acquirer_id', '=', order.payment_acquirer_id.id)],
                    limit=1
                )
            order.payment_token_id = payment_token_id and payment_token_id.id or False

    def get_transaction_amount(self):
        self.ensure_one()
        amount_total = 0.0
        for line in self.order_line:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            computed_qty = line.product_uom_qty - line.qty_invoiced
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                computed_qty,
                product=line.product_id,
                partner=line.order_id.partner_id
            )
            amount_total += taxes['total_included']
        return self.pricelist_id.currency_id.round(amount_total)

    def _get_total_transaction_amount(self):
        self.ensure_one()
        if self.payment_acquirer_id.backend_confirm == 'authorize_capture':
            return sum(self.transaction_ids.filtered(
                lambda t: t.state != 'cancel').mapped('amount'))
        else:
            return sum(self.transaction_ids.filtered(
                lambda t: t.state != 'cancel' and not t.payment_id).mapped('amount'))

    @api.multi
    def _prepare_payment_vals(self, transaction_amount):
        self.ensure_one()
        return {
            'amount': transaction_amount,
            'payment_date': fields.Date.context_today(self),
            'communication': self.origin or self.name,
            'partner_id': self.partner_invoice_id.id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
            'journal_id': self.payment_method_id.id,
            'payment_method_id': self.payment_method_id.inbound_payment_method_ids and self.payment_method_id.inbound_payment_method_ids[0].id,
            'payment_token_id': self.payment_token_id.id,
        }

    @api.multi
    def create_transaction(self):
        for order in self:
            if not (order.payment_method_id.payment_acquirer_id.provider == 'authorize'):
                continue
            if order.payment_acquirer_id.backend_confirm == 'none':
                continue
            if not order.payment_token_id:
                raise UserError(
                    _('Transaction needs a stored payment token/credit-card'))
            if order.transaction_ids.filtered(
                    lambda t: t.state == 'authorized'):
                raise UserError(
                    _('Open Transaction needs to be voided'))
            transaction_amount = order.get_transaction_amount()
            total_transaction_amount = order._get_total_transaction_amount()
            if total_transaction_amount < transaction_amount:
                if order.payment_acquirer_id.backend_confirm == 'authorize':
                    reference = "SO-%s-%s" % (
                        order.id,
                        datetime.now().strftime('%H%M%S')
                    )
                    tx = self.env['payment.transaction'].create({
                        'amount': transaction_amount,
                        'acquirer_id': order.payment_token_id.acquirer_id.id,
                        'type': 'server2server',
                        'currency_id': order.currency_id.id,
                        'reference': reference,
                        'payment_token_id': order.payment_token_id.id,
                        'partner_id': order.partner_id.id,
                        'partner_country_id': order.partner_id.country_id.id,
                        'sale_order_ids': [(6, 0, [order.id])] ,
                        'bk_order': True,
                    })

                    # Authorize only
                    transaction = AuthorizeAPI(tx.acquirer_id)
                    res = transaction.authorize(
                        tx.payment_token_id, tx.amount, tx.reference)

                    s2s_result = tx._authorize_s2s_validate_tree(res)

                    if not s2s_result or tx.state != 'authorized':
                        raise ValidationError(
                            _("Payment transaction failed (%s)") %
                            tx.state_message
                        )
                    order.payment_tx_id = tx
                elif order.payment_acquirer_id.backend_confirm == 'authorize_capture':
                    vals = order._prepare_payment_vals(transaction_amount)
                    payment = self.env['account.payment'].with_context(
                        sale_ids=[order.id]).create(vals)
                    payment.post()
                    payment.payment_transaction_id.sale_order_ids = [(6, 0, [order.id])]
                    order.payment_tx_id = payment.payment_transaction_id.id
            elif total_transaction_amount == transaction_amount:
                raise UserError(
                    _('Transaction already exists!'))
            else:
                raise UserError(
                    _('The Total amount available in Transactions exceeds the order amount'))

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if isinstance(res, bool) and not self._context.get('website_order_tx', False):
            self.create_transaction()
        return res

    @api.multi
    def _create_payment_transaction(self, vals):
        self = self.with_context(website_order_tx=True)
        tx = super(SaleOrder, self)._create_payment_transaction(vals)
        self.write({
            'payment_token_id': tx.payment_token_id and tx.payment_token_id.id or False,
            'payment_method_id': tx.acquirer_id and tx.acquirer_id.journal_id.id or False,
            'payment_tx_id' : tx.id or False,
            })
        return tx
