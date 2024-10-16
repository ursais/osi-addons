# Import Odoo libs
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"


    def _compute_values_company_diff(self):
        for product in self:
            values_company_diff = False
            # for attribute_value in product.product_template_variant_value_ids:
            #     print("======....///",attribute_value)
            #     if self.env.company.id not in attribute_value.company_ids.ids:
            #         values_company_diff = True
            product.values_company_diff = values_company_diff

    values_company_diff = fields.Boolean(default=False,copy=False,compute="_compute_values_company_diff")
 