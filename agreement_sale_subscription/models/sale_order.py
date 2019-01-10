# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def create_subscriptions(self):
        res = super(SaleOrder, self).create_subscriptions()
        for line in self.order_line:
            if line.subscription_id:
                self.agreement_id.subscription_id = line.subscription_id
                line.subscription_id.agreement_id = self.agreement_id
        return res
