# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Extend product.template with additional fields and logic for managing
    visibility in configuration wizard.
    """

    _inherit = "product.template"

    # COLUMNS ##########
    default_code = fields.Char(
        "Internal Reference",
        compute="",
        inverse="",
        store=True,
    )
    company_ids_display = fields.Many2many(
        "res.company",
        'product_template_company_display_rel',
        'product_temp_id'
        'company_id',
        string="Enabled Companies",
        help=(
            """Used for eCommerce: If set, the product is limited to be sold
            only in these regions."""
        ),
    )

    # END ##########
    # METHODS ##########

    def write(self, vals):
        # Check if 'default_code' is being updated
        if "default_code" in vals:
            new_default_code = vals["default_code"]
            for template in self:
                # Update default_code for all related products
                for product in template.product_variant_ids:
                    if template.config_ok:
                        product.default_code = f"{new_default_code}-{product.id}"
                    else:
                        product.default_code = new_default_code
        return super().write(vals)

    # END ##########
