# Import Odoo libs
from odoo import fields, models


class PurchaseCreationWizard(models.TransientModel):
    _name = "purchase.creation.wizard"
    _description = "Wizard to create RFQ"

    # COLUMNS ##########

    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        default=lambda self: self.env.context.get("default_product_id"),
    )

    # END ##########
    # METHODS ##########

    def action_create_purchase(self):
        self.ensure_one()
        purchase = self.env["mrp.eco"].browse(self._context.get("active_id"))
        action = purchase.action_create_purchase(self.partner_id, self.product_id)
        return action

    # END ##########
