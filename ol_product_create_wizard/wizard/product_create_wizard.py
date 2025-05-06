# Import Odoo libs
from odoo import api, fields, models


class ProductCreateWizard(models.TransientModel):
    """Create product wizard where user can create new product based on existing one."""

    _name = "product.create.wizard"
    _description = "Product Creation Wizard"

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
    internal_ref = fields.Char(
        string="Internal Reference",
        related="product_tmpl_id.default_code",
    )
    version = fields.Char(
        string="Version",
        required=True,
    )
    eco_type_id = fields.Many2one(
        comodel_name="mrp.eco.type",
        string="ECO Type",
        required=True,
    )

    # END ##########
    # METHODS ##########

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        product_tmpl_id = self.env.context.get("default_product_tmpl_id")
        if product_tmpl_id:
            product = self.env["product.template"].browse(product_tmpl_id)
            res["internal_ref"] = product.default_code or ""
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

    def action_confirm(self):
        # Duplicate product template
        new_template = self.product_tmpl_id.copy(
            {
                "name": f"{self.product_tmpl_id.name}",
                "default_code": f"{self.internal_ref}-{self.version}",
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
                    for line in self.attribute_line_ids
                ],
            }
        )

        apply_on = "product"
        if new_template.config_ok:
            new_template.action_create_rebuild_scaffolding_bom()
            bom = (
                self.env["mrp.bom"]
                .sudo()
                .search(
                    [
                        ("product_tmpl_id", "=", new_template.id),
                        ("scaffolding_bom", "=", True),
                    ]
                )
            )
            apply_on = "bom"

        # Get the first stage for the selected ECO type
        first_stage = self.env["mrp.eco.stage"].search(
            [("type_ids", "in", self.eco_type_id.id)],
            order="sequence",
            limit=1,
        )

        # Create an ECO for the new product template
        eco = self.env["mrp.eco"].create(
            {
                "name": f"{new_template.name} ECO",
                "type": apply_on,
                "type_id": self.eco_type_id.id,
                "stage_id": first_stage.id if first_stage else False,
                "product_tmpl_id": new_template.id,
                "bom_id": bom.id,
            }
        )

        # Redirect to the ECO form view
        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.eco",
            "res_id": eco.id,
            "view_mode": "form",
            "target": "current",
        }

    # END ##########
