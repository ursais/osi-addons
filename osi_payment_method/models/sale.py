# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit="sale.order"
                                          
    payment_method = fields.Many2one("custom.payment.method", string="Payment Method")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.payment_method = self.partner_id.payment_method

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder,self)._prepare_invoice()
        invoice_vals.update({'payment_method':self.payment_method.id})
        return invoice_vals