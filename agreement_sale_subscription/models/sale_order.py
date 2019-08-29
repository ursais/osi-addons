# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super()._action_confirm()
        for order in self:
            for line in order.order_line:
                if line.subscription_id and order.agreement_id:
                    order.agreement_id.subscription_id = \
                        line.subscription_id.id
                    line.subscription_id.agreement_id = \
                        order.agreement_id.id
        return res
