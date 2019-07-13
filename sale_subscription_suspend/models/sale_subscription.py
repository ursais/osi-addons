# Copyright (C) 2019 - TODAY, Open Source Integrators, Brian McMaster
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class SaleSubscription(models.Model):

    _inherit = 'sale.subscription'

    def action_suspend(self):
        return self.write({'stage_id': self.env.ref(
            'sale_subscription_suspend.sale_subscription_stage_suspend'
        ).id})

    def action_re_activate(self):
        return self.set_open()
