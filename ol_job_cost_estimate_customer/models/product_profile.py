from odoo import fields, models


class ProductProfile(models.Model):
    _inherit = "product.profile"

    detailed_type = fields.Selection(
        selection_add=[("product", "Storable Product")],
        ondelete={"product": "cascade"},
    )
