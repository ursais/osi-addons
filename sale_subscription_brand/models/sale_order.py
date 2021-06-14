# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def create_subscriptions(self):
        res = super(SaleOrder, self).create_subscriptions()
        for sub_id in res:
            subscription = self.env["sale.subscription"].search([("id", "=", sub_id)])
            subscription.brand = self.brand
