# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.multi
    def _prepare_purchase_order(self, product_id, product_qty, product_uom,
                                origin, values, partner):
        res = super()._prepare_purchase_order(
            product_id, product_qty, product_uom, origin, values, partner)
        if res:
            if not res.get('payment_journal_id', False):
                res.update({
                    'payment_journal_id':
                        partner.out_payment_journal_id and
                        partner.out_payment_journal_id.id or False})
            if not res.get('payment_method_id', False):
                res.update({
                    'payment_method_id':
                        partner.out_payment_method_id and
                        partner.out_payment_method_id.id or False})
        return res
