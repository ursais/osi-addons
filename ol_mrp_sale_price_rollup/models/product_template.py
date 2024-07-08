# Import Odoo libs
from odoo import models


class ProductTemplate(models.Model):
    """
    Inherit Product for Method Overriding.
    """

    _inherit = "product.template"

    # METHODS ##########

    def action_bom_sale_price(self):
        """Action to set sale price on template level if single variant."""
        templates = self.filtered(
            lambda t: t.product_variant_count == 1 and t.bom_count > 0
        )
        if templates:
            return templates.mapped("product_variant_id").action_bom_sale_price()

    def button_bom_sale_price(self):
        """Button action to set sale price on template level if single variant."""
        templates = self.filtered(
            lambda t: t.product_variant_count == 1 and t.bom_count > 0
        )
        if templates:
            return templates.mapped("product_variant_id").button_bom_sale_price()

    # END #########
