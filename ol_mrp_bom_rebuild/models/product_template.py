from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _reset_all_variants_bom_with_master_bom(self):
        for template in self:
            template.product_variant_ids._reset_variant_bom_with_master_bom()
