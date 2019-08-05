# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    payment_method = fields.Many2one("account.payment.method",
                                     string="Payment Method")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        self.payment_method = self.partner_id.payment_method
        return res

    @api.multi
    def action_view_invoice(self):
        res = super().action_view_invoice()
        res['context']['default_payment_method'] = self.payment_method.id
        return res


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_order(self, product_id, product_qty, product_uom,
                                origin, values, partner):
        res = super()._prepare_purchase_order(
            product_id, product_qty, product_uom, origin, values, partner)
        if res and 'payment_method' not in res:
            res.update({'payment_method': partner.payment_method and
                        partner.payment_method.id or False})
        return res
