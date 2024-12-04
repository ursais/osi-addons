from odoo import models, fields, api


class ProductCreationWizard(models.TransientModel):
    _name = "product.creation.wizard"
    _description = "Wizard to create product, BoM, and ECO"

    product_name = fields.Char(string="Product Name", required=True)

    def action_create_product_bom_eco(self):
        self.ensure_one()
        sale_estimate_job = self.env["sale.estimate.job"].browse(
            self._context.get("active_id")
        )
        action = sale_estimate_job.action_create_eco_and_product(self.product_name)
        return action
