# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

from odoo import models, fields, api
from werkzeug import url_encode


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_token_id = fields.Many2one(
        'payment.token',
        string="Saved payment token",
        help='Lists the Payment Tokens available',
        copy=False,
    )

    @api.multi
    def payment_url_invoice(self):
        self.ensure_one()
        self.partner_id.validate_partner()
        values_to_pass = dict(self._context.get('params', {}))
        values_to_pass.update({
            'model': self._name,
            'id': self.id,
        })
        final_url = "user/payment_method/%s/?%s" % (
            self.partner_id.id, url_encode(values_to_pass))
        return {
            'type': 'ir.actions.act_url',
            'url': final_url,
            'nodestroy': True,
            'target': 'self'
        }
