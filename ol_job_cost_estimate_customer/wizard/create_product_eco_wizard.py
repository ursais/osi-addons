# Import Odoo libs
from odoo import api, fields, models


class ProductCreationWizard(models.TransientModel):
    _name = "product.creation.wizard"
    _description = "Wizard to create product, BoM, and ECO"

    # COLUMNS #####

    product_name = fields.Char(string="Product Name", required=True)
    type_id = fields.Many2one("mrp.eco.type", "ECO Type")

    # END #########

    # METHODS #####

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        eco_type = self.env["mrp.eco.type"].search([("name", "=", "New SKU")], limit=1)
        if eco_type:
            if "type_id" in fields:
                result["type_id"] = eco_type.id
        return result

    def action_create_product_bom_eco(self):
        self.ensure_one()
        sale_estimate_job = self.env["sale.estimate.job"].browse(
            self._context.get("active_id")
        )
        action = sale_estimate_job.action_create_eco_and_product(
            self.product_name, self.type_id
        )
        return action

    # END #########
