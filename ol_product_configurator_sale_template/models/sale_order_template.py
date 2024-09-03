# Import Odoo libs
from odoo import models


class SaleOrderTemplate(models.Model):
    """
    Add new methods to Sale Order Template
    """

    _inherit = "sale.order.template"

    # METHODS ##########

    def action_config_start(self):
        """Return action to start configuration wizard"""
        configurator_obj = self.env["product.configurator.sale.order.temp"]
        ctx = dict(
            self.env.context,
            default_order_id=self.id,
            wizard_model="product.configurator.sale.order.temp",
            allow_preset_selection=True,
        )
        return configurator_obj.with_context(**ctx).get_wizard_action()

    # END ##########
