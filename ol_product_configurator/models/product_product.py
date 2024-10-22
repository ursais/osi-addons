# Import Odoo libs
from odoo import fields, models


class ProductProduct(models.Model):
    """
    Inherit the Product Variant Object Adding Fields and Methods
    """

    _inherit = "product.product"

    # COLUMNS ##########

    values_company_diff = fields.Boolean(
        default=False, copy=False, compute="_compute_values_company_diff"
    )

    # END ##########
    # METHODS ##########

    def _compute_values_company_diff(self):
        """Helper method to determine whether to show the banner
        on the product form view."""
        for product in self:
            values_company_diff = False
            for attribute_value in product.product_template_variant_value_ids:
                # Check if company_ids is set and if the user's company is
                # not in company_ids
                if (
                    attribute_value.company_ids
                    and self.env.company.id not in attribute_value.company_ids.ids
                ):
                    values_company_diff = True
                    # No need to continue checking once it's set to True
                    break
            product.values_company_diff = values_company_diff

    # END ##########
