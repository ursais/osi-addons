# Import Odoo libs
from odoo import models


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def create_get_variant(self, value_ids=None, custom_vals=None):
        """Inherit the method to set the sales price from
        bom when configured/created."""
        variant = super().create_get_variant(
            value_ids=value_ids,
            custom_vals=custom_vals,
        )
        variant._set_sale_price_from_bom()
        return variant
