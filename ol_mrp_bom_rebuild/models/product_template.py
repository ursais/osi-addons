# Import Odoo libs
from odoo import models


class ProductTemplate(models.Model):
    """
    Inherit Product Template, adding Rebuild All Variants From BoM method.
    """

    _inherit = "product.template"

    # METHODS #####

    def _reset_all_variants_bom_with_scaffold_bom(self):
        """Method called by button or server action which cycles through all
        related variants on the template and runs the rebuild BoM method."""
        for template in self:
            variants = template.product_variant_ids.filtered(
                lambda x: x.product_template_variant_value_ids != []
            )
            for variant in variants:
                variant._reset_variant_bom_with_scaffold_bom()

    # END #########
