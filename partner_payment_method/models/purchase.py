# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    payment_method = fields.Many2one("partner.payment.method",
                                     string="Preferred Payment Method")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.payment_method = self.partner_id.payment_method

    @api.multi
    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_payment_method'] = self.payment_method.id
        return result
