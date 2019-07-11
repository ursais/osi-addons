# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    payment_method = fields.Many2one("custom.payment.method",
                                     string="Payment Method")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.payment_method = self.partner_id.payment_method

    @api.multi
    def action_view_invoice(self):
        result = super(PurchaseOrder, self).action_view_invoice()
        result['context']['default_payment_method'] = self.payment_method.id
        return result


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_order(self, product_id, product_qty, product_uom,
                                origin, values, partner):
        res = super(StockRule, self)._prepare_purchase_order(
            product_id, product_qty, product_uom, origin, values, partner)
        if res and 'payment_method' not in res:
            res.update({'payment_method': partner.payment_method and
                        partner.payment_method.id or False})
        return res
