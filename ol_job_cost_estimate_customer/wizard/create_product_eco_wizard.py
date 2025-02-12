# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductCreationWizard(models.TransientModel):
    _name = "product.creation.wizard"
    _description = "Wizard to create product, BoM, and ECO"

    # COLUMNS #####

    estimate_id = fields.Many2one(
        comodel_name="sale.estimate.job",
        string="Estimate",
    )
    product_name = fields.Char(
        string="Product Name",
        required=True,
    )
    eco_type_id = fields.Many2one(
        comodel_name="mrp.eco.type",
        string="ECO Type",
        required=True,
    )
    product_type = fields.Selection(
        [
            ("prototype_system", "Prototype System"),
            ("prototype_component", "Prototype Component"),
            ("service", "Service"),
        ],
        string="Product Type",
        required=True,
    )

    # END #########

    # METHODS #####

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        eco_type = self.env["mrp.eco.type"].search([("name", "=", "New SKU")], limit=1)
        if eco_type:
            if "eco_type_id" in fields:
                result["eco_type_id"] = eco_type.id
        return result

    def action_create_product_bom_eco(self):
        """Creates a new product and corresponding ECO, and optionally a BOM."""
        ProductTemplate = self.env["product.template"]
        MrpEco = self.env["mrp.eco"]
        MrpBom = self.env["mrp.bom"]
        MrpBomLine = self.env["mrp.bom.line"]
        ProductProfile = self.env["product.profile"]
        EcoStage = self.env["mrp.eco.stage"]

        # Added the validation for Prototype Product Name Duplication
        if self.product_type == "prototype_system":
            list_product = (
                self.estimate_id.estimate_ids.filtered(
                    lambda l: not l.product_id.candidate_bom
                )
                .mapped("product_id")
                .mapped("name")
            )
            if any(self.product_name.lower() == name.lower() for name in list_product):
                raise UserError(
                    _(
                        "The product [%s] on the estimate that is not allowed to be on a BoM."
                        "Please update the estimate line and try again."
                        % (self.product_name)
                    )
                )

        # Fetch common ECO stage
        eco_stage = EcoStage.search([("type_ids", "in", self.eco_type_id.id)], limit=1)

        # Initialize variables
        new_product = None
        new_eco = None
        new_bom = None
        eco_apply_on = "product"  # Default ECO type

        # Product creation logic based on type
        product_data = {"name": self.product_name, "estimate_id": self.estimate_id.id}
        if self.product_type == "service":
            product_data["detailed_type"] = "service"
        elif self.product_type == "prototype_component":
            profile = ProductProfile.search(
                [("name", "=", "Prototype Component")], limit=1
            )
            product_data["profile_id"] = profile.id
        elif self.product_type == "prototype_system":
            profile = ProductProfile.search([("name", "=", "Prototype")], limit=1)
            product_data["profile_id"] = profile.id
        new_product = ProductTemplate.create(product_data)

        # BOM and ECO creation for prototype systems
        if self.product_type == "prototype_system":
            # Create BOM
            new_bom = MrpBom.create(
                {
                    "product_tmpl_id": new_product.id,
                    "scaffolding_bom": True,
                    "type": "normal",
                }
            )
            # Create BOM lines in bulk
            bom_lines = [
                {
                    "bom_id": new_bom.id,
                    "product_id": line.product_id.id,
                    "product_qty": line.product_uom_qty,
                }
                for line in self.estimate_id.estimate_ids
            ]
            MrpBomLine.create(bom_lines)
            eco_apply_on = "bom"

        # ECO creation
        eco_data = {
            "name": self.product_name,
            "type_id": self.eco_type_id.id,
            "type": eco_apply_on,
            "product_tmpl_id": new_product.id,
            "estimate_id": self.estimate_id.id,
            "stage_id": eco_stage.id,
        }
        if new_bom:
            eco_data["bom_id"] = new_bom.id
        new_eco = MrpEco.create(eco_data)

        # Show the created ECO
        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.eco",
            "view_mode": "form",
            "res_id": new_eco.id,
            "target": "current",
        }

    # END #########
