# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def create_subscriptions(self):
        for order in self:
            res = super(SaleOrder, order).create_subscriptions()
            for sub_id in res:
                subscription = self.env['sale.subscription'].browse(sub_id)
                subscription.brand_id = order.brand_id.id
        return res
