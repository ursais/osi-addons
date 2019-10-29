# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_method_id = fields.Many2one(
        'account.journal',
        string='Payment Method',
        domain=[
            ('at_least_one_inbound', '=', True),
            ('type', 'in', ['bank', 'cash'])
        ],
        copy=False,
    )
    payment_acquirer_id = fields.Many2one(
        'payment.acquirer',
        string='Payment Acquirer',
        copy=False,
    )
    payment_token_id = fields.Many2one(
        'payment.token',
        string="Saved payment token",
        help='Lists the Payment Tokens available',
        copy=False,
    )
    payment_tx_id = fields.Many2one(
        'payment.transaction',
        string='Payment Transaction',
        copy=False
    )
    real_payment_tx_id = fields.Many2one(
        'payment.transaction',
        compute='compute_real_payment_tx_id',
        string='Payment Transaction used in Register payment',
        copy=False
    )
    sale_ids = fields.Many2many(
        'sale.order',
        string="Sale Order",
        compute='_get_saleorder',
        store=True,
        readonly=True,
        copy=False)
    hide_addcard = fields.Boolean(
        compute='_compute_hide_addcard'
    )

    @api.multi
    @api.depends('payment_method_id')
    def _compute_hide_addcard(self):
        authorize_journals = self.env['account.journal'].sudo().search(
            [('payment_acquirer_id.provider', '=', 'authorize')])
        for invoice in self:
            invoice.hide_addcard = True
            if invoice.payment_method_id.id in authorize_journals.ids:
                invoice.hide_addcard = False

    @api.depends('invoice_line_ids')
    def _get_saleorder(self):
        for invoice in self:
            sale_ids = invoice.invoice_line_ids.mapped(
                'sale_line_ids').mapped('order_id')
            invoice.sale_ids = sale_ids

    @api.depends('payment_ids', 'payment_tx_id', 'type')
    def compute_real_payment_tx_id(self):
        for invoice in self:
            if invoice.type != 'out_invoice':
                invoice.real_payment_tx_id = False
                continue
            payment_tx_id = invoice.payment_tx_id
            if invoice.payment_tx_id.payment_id:
                payment_tx_id = self.env['payment.transaction'].search(
                    [('payment_token_id', '=', invoice.payment_token_id.id),
                     ('sale_order_ids', '=', invoice.sale_ids.ids and invoice.sale_ids.ids[0]),
                     ('state', '!=', 'cancel'),
                     ('payment_id', '=', False)],
                    limit=1,
                )
            invoice.real_payment_tx_id = payment_tx_id

    @api.onchange('payment_method_id')
    def onchange_payment_method_id(self):
        for invoice in self:
            if invoice.payment_method_id.is_electronic_payment_method:
                if invoice.payment_method_id.payment_acquirer_id:
                    invoice.payment_acquirer_id = invoice.payment_method_id.payment_acquirer_id.id
                else:
                    raise UserError(
                        _('The Payment Acquirer is not selected in the Payment Method!'))
