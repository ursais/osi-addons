# Copyright (C) 2019, Open Source Integrators
# Copyright (C) 2019, Brian McMaster
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import models


class SaleSubscription(models.Model):

    _inherit = "sale.subscription"

    def action_suspend(self):
        return self.write({"stage_id": self.env.ref(
            "sale_subscription_suspend.sale_subscription_stage_suspend"
        ).id})

    def action_re_activate(self):
        subscription_stage_obj = self.env["sale.subscription.stage"]
        for sub in self:
            stage = subscription_stage_obj.search(
                [("in_progress", "=", True)], limit=1)
            sub.write({"stage_id": stage.id, "to_renew": False, "date": False})
