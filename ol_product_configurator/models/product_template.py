# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Extend product.template with additional fields and logic for managing
    visibility in configuration wizard.
    """

    _inherit = "product.template"

    # COLUMNS ##########
    default_code = fields.Char(
        string="Internal Reference",
        compute="",
        inverse="",
        store=True,
    )
    company_ids_display = fields.Many2many(
        comodel_name="res.company",
        relation="product_template_company_display_rel",
        column1="product_template_id",
        column2="company_id",
        string="Enabled Companies",
        help=(
            "Used for eCommerce: If set, the product is limited to be sold "
            "only in these regions."
        ),
    )

    has_advanced_configuration = fields.Boolean(
        compute="_compute_has_advanced_configuration",
        store=True,
    )

    # END ##########
    # METHODS ##########

    @api.depends(
        "config_line_ids",
        "bom_ids.scaffolding_bom",
        "bom_ids.bom_line_ids.config_set_id",
    )
    def _compute_has_advanced_configuration(self):
        """
        Compute the `has_advanced_configuration` field:
        - True if there are any `config_line_ids`
        - True if the product has a scaffolding BoM with at least one component
          missing `config_set_id`
        - False otherwise
        """
        for product in self:
            product.has_advanced_configuration = bool(
                product.config_line_ids
                or any(
                    bom.scaffolding_bom
                    and any(not line.config_set_id for line in bom.bom_line_ids)
                    for bom in product.bom_ids
                )
            )

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
