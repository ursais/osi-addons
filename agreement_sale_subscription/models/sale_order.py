# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def create_subscriptions(self):
        res = super().create_subscriptions()
        for order in self:
            for line in order.order_line:
                if line.subscription_id and order.agreement_id:
                    # Set the subscription on the agreement
                    order.agreement_id.subscription_id = \
                        line.subscription_id.id
                    # Set the agreement on the subscription
                    line.subscription_id.agreement_id = order.agreement_id.id
        return res
