# Import Odoo libs
from odoo import api, fields, models


class SaleEstimateJob(models.Model):
    """Add button to create new ECO/Product/BoM for Prototypes."""

    _inherit = "sale.estimate.job"

    # COLUMNS ######

    product_tmpl_ids = fields.One2many(
        "product.template",
        "estimate_id",
        string="Product Templates",
    )
    product_count = fields.Integer(
        string="Prototype Count",
        compute="_compute_product_count",
    )
    mrp_eco_ids = fields.One2many(
        "mrp.eco",
        "estimate_id",
        string="ECOs",
    )
    mrp_eco_count = fields.Integer(
        string="ECO Count",
        compute="_compute_mrp_eco_count",
    )

    # END ##########
    # METHODS ##########

    def open_product_creation_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "product.creation.wizard",
            "view_mode": "form",
            "target": "new",
        }

    def action_create_eco_and_product(self, product_name, type):
        """Action called via button to create a new prototype product."""
        # Create the estimate
        profile = self.env["mrp.eco.type"].search([("name", "=", "Prototype")], limit=1)
        new_product = self.env["product.template"].create(
            {
                "name": product_name,
                "profile_id": profile.id,
                "estimate_id": self.id,
            }
        )

        new_bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": new_product.id,
                "scaffolding_bom": True,
                "type": "normal",
            }
        )
        # Populate BOM lines based on estimate lines
        for line in self.estimate_ids:
            self.env["mrp.bom.line"].create(
                {
                    "bom_id": new_bom.id,
                    "product_id": line.product_id.id,
                    "product_qty": line.product_uom_qty,
                }
            )

        # Create ECO
        eco_stage = self.env["mrp.eco.stage"].search(
            [("type_ids", "in", type.id)], limit=1
        )
        new_eco = self.env["mrp.eco"].create(
            {
                "name": product_name,
                "type_id": type.id,
                "type": "bom",
                "product_tmpl_id": new_product.id,
                "bom_id": new_bom.id,
                "estimate_id": self.id,
                "stage_id": eco_stage.id,
            }
        )
        # Show the created eco
        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.eco",
            "view_mode": "form",
            "res_id": new_eco.id,
            "target": "current",
        }

    @api.depends("product_tmpl_ids")
    def _compute_product_count(self):
        """Standard count method to count related Products's for smart button."""
        for lead in self:
            lead.product_count = len(lead.product_tmpl_ids)

    def action_view_product(self):
        """Smart button action to open the Product or list of Products if
        more than one."""
        products = self.product_tmpl_ids
        action = self.env.ref("product.product_template_action").read()[0]
        if len(products) == 1:
            # Open the single product in form view
            action["views"] = [
                (self.env.ref("product.product_template_only_form_view").id, "form"),
            ]
            action["res_id"] = products.id
        else:
            # Open the list view with a fallback to form view for individual records
            action["views"] = [
                (self.env.ref("product.product_template_tree_view").id, "tree"),
                (self.env.ref("product.product_template_only_form_view").id, "form"),
            ]
            action["context"] = dict(self.env.context)  # Preserve context if needed
            action["domain"] = [("id", "in", products.ids)]

        return action

    @api.depends("mrp_eco_ids")
    def _compute_mrp_eco_count(self):
        """Standard count method to count related ECO's for smart button."""
        for lead in self:
            lead.mrp_eco_count = len(lead.mrp_eco_ids)

    def action_view_eco(self):
        """Smart button action to open the ECO or list of ECO's if more than one."""
        ecos = self.mrp_eco_ids
        action = self.env.ref("mrp_plm.mrp_eco_action").read()[0]

        if len(ecos) == 1:
            # Open the single ECO in form view
            action["views"] = [
                (self.env.ref("mrp_plm.mrp_eco_view_form").id, "form"),
            ]
            action["res_id"] = ecos.id
        else:
            # Open the list view with a fallback to form view for individual records
            action["views"] = [
                (self.env.ref("mrp_plm.mrp_eco_view_tree").id, "tree"),
                (self.env.ref("mrp_plm.mrp_eco_view_form").id, "form"),
            ]
            action["domain"] = [("id", "in", ecos.ids)]
            action["context"] = dict(self.env.context)  # Preserve context if needed

        return action
