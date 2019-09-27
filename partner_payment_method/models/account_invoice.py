# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    payment_method = fields.Many2one("partner.payment.method",
                                     string="Preferred Payment Method")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.payment_method = self.partner_id.payment_method

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if self._context.get('default_payment_method', False):
            self.payment_method = self.purchase_id.payment_method.id
        return super(AccountInvoice, self).purchase_order_change()
