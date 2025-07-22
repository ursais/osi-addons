# Import Odoo libs
from odoo import models


class ProductTemplate(models.Model):
    """
    Inherit Product Template, adding Rebuild All Variants From BoM method.
    """

    _inherit = "product.template"

    # METHODS #####

    def _reset_all_variants_bom_with_scaffold_bom(self):
        """
        Method called by button or server action which cycles through all
        related variants on the template and runs the rebuild BoM method.

        If queuing is enabled the variant rebuilds will go through the job queue.
        """
        enable_delay = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("ol_mrp_bom_rebuild.enable_delay_variant_bom_rebuild")
        )
        for template in self:
            variants = template.product_variant_ids.filtered(
                lambda x: x.product_template_variant_value_ids != []
            )
            for variant in variants:
                if enable_delay == "True":
                    variant.with_delay()._reset_variant_bom_with_scaffold_bom()
                else:
                    variant._reset_variant_bom_with_scaffold_bom()

    # END #########
