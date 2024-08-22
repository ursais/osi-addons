# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleBlanketOrder(models.Model):
    _inherit = "sale.blanket.order"

    def action_config_start(self):
        """Return action to start configuration wizard"""
        configurator_obj = self.env["product.configurator.sale.blanket.order"]
        ctx = dict(
            self.env.context,
            default_order_id=self.id,
            wizard_model="product.configurator.sale.blanket.order",
            allow_preset_selection=True,
        )
        return configurator_obj.with_context(**ctx).get_wizard_action()
