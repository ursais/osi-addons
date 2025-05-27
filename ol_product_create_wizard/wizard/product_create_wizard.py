# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

SYSTEM_TIERS = [
    ("normal", "Normal System"),
    ("custom_created", "Custom Created System"),
    ("customer", "Customer System"),
]


class ProductCreateWizard(models.TransientModel):
    """Create product wizard where user can create new product based on existing one."""

    _name = "product.create.wizard"
    _description = "Product Creation Wizard"
    _rec_name = "internal_ref"

    # COLUMNS ##########

    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        required=True,
    )
    attribute_line_ids = fields.One2many(
        comodel_name="product.create.wizard.line",
        inverse_name="wizard_id",
        string="Attribute Lines",
    )
    product_name = fields.Char(
        string="Product Name",
        required=True,
    )
    internal_ref = fields.Char(
        string="Internal Reference",
        related="product_tmpl_id.default_code",
    )
    prefix = fields.Char(
        string="Prefix",
        required=True,
    )
    eco_type_id = fields.Many2one(
        comodel_name="mrp.eco.type",
        string="ECO Type",
        required=True,
    )
    public_destination = fields.Selection(
        [
            ("not_public", "Not Public"),
            ("b2b", "B2B"),
            ("b2c", "B2C"),
            ("b2b_b2c", "B2B + B2C"),
        ],
        string="Public Destination",
        default="not_public",
    )
    allow_backorder = fields.Boolean(
        default=True,
        company_dependent=True,
    )
    company_ids_display = fields.Many2many(
        comodel_name="res.company",
        string="Enabled Companies",
        help=(
            "Used for eCommerce: If set, the product is limited to be sold "
            "only in these regions."
        ),
    )
    system_tier = fields.Selection(
        selection=SYSTEM_TIERS,
        string="System Tier",
        default="customer",
    )

    # END ##########
    # METHODS ##########

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        product_tmpl_id = self.env.context.get("default_product_tmpl_id")
        default_eco = (
            self.env["mrp.eco.type"]
            .sudo()
            .search([("name", "=", "New System Enablement")], limit=1)
        )
        res["eco_type_id"] = default_eco.id if default_eco else False
        if product_tmpl_id:
            product = self.env["product.template"].browse(product_tmpl_id)
            res["product_name"] = product.name
            res["internal_ref"] = product.default_code or ""
            # res["public_destination"] = product.public_destination
            # res["company_id"] = False
            # res["system_tier"] = product.name
            res["allow_backorder"] = product.allow_backorder
            res["company_ids_display"] = [(6, 0, product.company_ids_display.ids)]
            res["attribute_line_ids"] = [
                (
                    0,
                    0,
                    {
                        "attribute_id": line.attribute_id.id,
                        "value_ids": [(6, 0, line.value_ids.ids)],
                        "used_in_sale_description": line.used_in_sale_description,
                        "is_qty_required": line.is_qty_required,
                        "default_val": line.default_val.id,
                        "required": line.required,
                        "multi": line.multi,
                        "custom": line.custom,
                    },
                )
                for line in product.product_tmpl_id.attribute_line_ids
            ]
        return res

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        if not self.product_tmpl_id:
            return

        self.attribute_line_ids = [(5, 0, 0)]  # Clear existing lines

        self.attribute_line_ids = [
            (
                0,
                0,
                {
                    "attribute_id": line.attribute_id.id,
                    "value_ids": [(6, 0, line.value_ids.ids)],
                    "used_in_sale_description": line.used_in_sale_description,
                    "is_qty_required": line.is_qty_required,
                    "default_val": line.default_val.id,
                    "required": line.required,
                    "multi": line.multi,
                    "custom": line.custom,
                },
            )
            for line in self.product_tmpl_id.attribute_line_ids
        ]
        self.product_name = self.product_tmpl_id.name
        self.public_destination = self.product_tmpl_id.public_destination
        self.allow_backorder = self.product_tmpl_id.allow_backorder
        self.company_ids_display = [
            (6, 0, self.product_tmpl_id.company_ids_display.ids)
        ]

    def check_duplicate_default_code(self, code_to_check):
        """
        Check if a product.template exists with a case-insensitive match
        for default_code. Raise ValidationError if a duplicate is found
        and it's not the current one.
        """
        if not code_to_check:
            return

        duplicate = self.env["product.template"].search(
            [
                ("default_code", "ilike", code_to_check),
                ("id", "not in", self.mapped("product_tmpl_id").ids),
            ],
            limit=1,
        )

        if duplicate:
            raise ValidationError(
                _(
                    "A product with internal reference '%s' already exists."
                    " Please choose a different prefix"
                )
                % duplicate.default_code
            )

    def action_confirm(self):
        """
        Action to confirm and:
        1. Check for duplicate default_code.
        2. Duplicate the product.template.
        3. Create a BOM if necessary.
        4. Create an ECO for the new template.
        5. Redirect to the ECO form view.
        """
        results = []
        for record in self:
            # Step 1: Compute and check for duplicate default_code
            new_default_code = f"{record.prefix}-{record.internal_ref}"
            record.check_duplicate_default_code(new_default_code)

            # Step 2: Duplicate product template with custom attributes
            new_template = record.product_tmpl_id.copy(
                {
                    "name": record.product_name,
                    "default_code": new_default_code,
                    "public_destination": record.public_destination,
                    "system_tier": record.system_tier,
                    "company_id": False,
                    "allow_backorder": record.allow_backorder,
                    "company_ids_display": [(5, 0, record.company_ids_display.ids)],
                    "attribute_line_ids": [(5, 0, 0)]
                    + [
                        (
                            0,
                            0,
                            {
                                "attribute_id": line.attribute_id.id,
                                "value_ids": [(6, 0, line.value_ids.ids)],
                                "used_in_sale_description": line.used_in_sale_description,
                                "is_qty_required": line.is_qty_required,
                                "default_val": line.default_val.id,
                                "required": line.required,
                                "multi": line.multi,
                                "custom": line.custom,
                            },
                        )
                        for line in record.attribute_line_ids
                    ],
                }
            )

            apply_on = "product"

            # Step 2.5: Copy attribute value line metadata
            original_tmpl = record.product_tmpl_id
            new_tmpl = new_template

            for new_attr_line in new_tmpl.attribute_line_ids:
                orig_attr_line = original_tmpl.attribute_line_ids.filtered(
                    lambda l: l.attribute_id.id == new_attr_line.attribute_id.id
                )
                if orig_attr_line.is_qty_required == new_attr_line.is_qty_required:
                    for new_val in new_attr_line.product_template_value_ids:
                        orig_val_line = (
                            orig_attr_line.product_template_value_ids.filtered(
                                lambda v: v.product_attribute_value_id.id
                                == new_val.product_attribute_value_id.id
                            )
                        )
                        if orig_val_line:
                            new_val.write(
                                {
                                    "is_qty_required": orig_val_line.is_qty_required,
                                    "default_qty": orig_val_line.default_qty,
                                    "maximum_qty": orig_val_line.maximum_qty,
                                }
                            )

            # Step 3: Create BOM if product is configurable
            if new_template.config_ok:
                new_template.action_create_rebuild_scaffolding_bom()
                bom = (
                    record.env["mrp.bom"]
                    .sudo()
                    .search(
                        [
                            ("product_tmpl_id", "=", new_template.id),
                            ("scaffolding_bom", "=", True),
                        ],
                        limit=1,
                    )
                )
                apply_on = "bom"
            else:
                bom = False

            # Determine if an ECO is needed
            original_lines = {
                line.attribute_id.id: set(line.value_ids.ids)
                for line in original_tmpl.attribute_line_ids
            }
            new_lines = {
                line.attribute_id.id: set(line.value_ids.ids)
                for line in record.attribute_line_ids
            }

            # Check if any lines were added or removed
            original_keys = set(original_lines.keys())
            new_keys = set(new_lines.keys())

            lines_added = new_keys - original_keys
            lines_removed = original_keys - new_keys

            eco_needed = bool(lines_added or lines_removed)

            # Check for added values in existing lines
            if not eco_needed:
                for attr_id in original_keys & new_keys:
                    original_vals = original_lines[attr_id]
                    new_vals = new_lines[attr_id]
                    if new_vals - original_vals:  # values added
                        eco_needed = True
                        break

            # Step 4: Get first ECO stage for selected ECO type
            eco = False
            if eco_needed:
                first_stage = record.env["mrp.eco.stage"].search(
                    [("type_ids", "in", record.eco_type_id.id)],
                    order="sequence",
                    limit=1,
                )

                # Step 5: Create an ECO
                eco = record.env["mrp.eco"].create(
                    {
                        "name": f"{new_template.name} ECO",
                        "type": apply_on,
                        "type_id": record.eco_type_id.id,
                        "stage_id": first_stage.id if first_stage else False,
                        "product_tmpl_id": new_template.id,
                        "bom_id": bom.id if bom else False,
                    }
                )

                # Redirect to ECO form view
                results.append(
                    {
                        "type": "ir.actions.act_window",
                        "res_model": "mrp.eco",
                        "res_id": eco.id,
                        "view_mode": "form",
                        "target": "current",
                    }
                )
            else:
                # Change product state to original since no ECO was needed.
                new_template.sudo().write(
                    {"product_state_id": self.product_tmpl_id.product_state_id.id}
                )

                # Redirect to Product Template form view
                results.append(
                    {
                        "type": "ir.actions.act_window",
                        "res_model": "product.template",
                        "res_id": new_template.id,
                        "view_mode": "form",
                        "target": "current",
                    }
                )

        # Return the first result (assumes one record at a time unless adapted to support multiple)
        return results[0] if results else True

    # END ##########
