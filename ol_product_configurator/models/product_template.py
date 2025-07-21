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
    has_advanced_configuration = fields.Text(
        string="Has Advanced Configurations",
        compute="_compute_has_advanced_configuration",
        store=True,
        readonly=True,
    )

    # END ##########
    # METHODS ##########

    @api.depends(
        "config_line_ids",
        "bom_ids.scaffolding_bom",
        "bom_ids.type",
        "bom_ids.bom_line_ids.config_set_id",
        "attribute_line_ids.multi",
        "attribute_line_ids.custom",
    )
    def _compute_has_advanced_configuration(self):
        """
        Compute reasons for advanced configuration:
        - True if Multi or Custom attribute lines are set
        - True if there are any config_line_ids
        - True if scaffolding BoM and not kit, has lines missing config_set_id
        """
        for product in self:
            # Skip non-configurable products
            if not product.attribute_line_ids:
                product.has_advanced_configuration = ""
                continue

            reasons = []

            # Reason 1: Config Lines Exist
            if product.config_line_ids:
                reasons.append("- Has Configuration Restrictions defined.")

            # Reason 2: If scaffold bom contains lines without config set and isn't kit
            if any(
                bom.scaffolding_bom
                and bom.type != "phantom"
                and any(not line.config_set_id for line in bom.bom_line_ids)
                for bom in product.bom_ids
            ):
                reasons.append(
                    "- Scaffolding BoM has one or more lines missing the Configuration Set."
                )

            # Reason 3: Multi Attributes Exist
            if any(line.multi for line in product.attribute_line_ids):
                reasons.append("- One or more attributes marked as Multi.")

            # Reason 4: Custom Attributes Exist
            if any(line.custom for line in product.attribute_line_ids):
                reasons.append("- One or more attributes marked as Custom.")

            product.has_advanced_configuration = "\n".join(reasons) if reasons else ""

    def action_create_rebuild_scaffolding_bom(self):
        # Models
        Bom = self.env["mrp.bom"]
        BomLine = self.env["mrp.bom.line"]
        BomLineConfig = self.env["mrp.bom.line.configuration"]
        BomLineConfigSet = self.env["mrp.bom.line.configuration.set"]
        ProductTemplateAttributeLine = self.env["product.template.attribute.line"]

        for product_template in self:
            existing_scaffold_bom = Bom.search(
                [
                    ("product_tmpl_id", "=", product_template.id),
                    ("scaffolding_bom", "=", True),
                ]
            )
            if existing_scaffold_bom:
                existing_scaffold_bom.write({"active": False})

            # Get the next version number
            # Get the next version number
            next_version = (
                existing_scaffold_bom.version if existing_scaffold_bom else 0
            ) + 1

            # Find all attribute lines related to the selected product template
            attribute_lines = ProductTemplateAttributeLine.search(
                [("product_tmpl_id", "=", product_template.id)]
            )

            # Create a Bill of Materials for the product template
            bom_vals = {
                "product_tmpl_id": product_template.id,
                "product_qty": 1.0,
                "type": "normal",  # Choose 'normal' or 'phantom' depending on your need
                "scaffolding_bom": True,
                "version": next_version,
            }
            new_bom = Bom.create(bom_vals)

            # Add BoM lines for each product associated with the attribute values
            for line in attribute_lines:
                attribute_values = line.value_ids
                for value in attribute_values:
                    product = value.product_id
                    if product:
                        # Attempt to find an existing configuration set
                        bom_line_config_set = BomLineConfigSet.search(
                            [("name", "=", product.display_name)], limit=1
                        )
                        # If not found, create a new one
                        if not bom_line_config_set:
                            bom_line_config_set = BomLineConfigSet.create(
                                {"name": product.display_name}
                            )

                        # Ensure value_ids is a list of IDs
                        value_ids = [value.id] if value else []

                        # Create the configuration
                        if value_ids:
                            existing_bom_line_config = BomLineConfig.search(
                                [
                                    ("config_set_id", "=", bom_line_config_set.id),
                                    (
                                        "value_ids",
                                        "in",
                                        value.id,
                                    ),
                                ]
                            )
                            if not existing_bom_line_config:
                                BomLineConfig.create(
                                    {
                                        "config_set_id": bom_line_config_set.id,
                                        "value_ids": [(6, 0, value_ids)],
                                    }
                                )

                        bom_line_vals = {
                            "bom_id": new_bom.id,
                            "product_id": product.id,
                            "product_qty": 1.0,  # Set the quantity needed for this product in the BoM
                            "config_set_id": bom_line_config_set.id,
                        }
                        BomLine.create(bom_line_vals)

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
