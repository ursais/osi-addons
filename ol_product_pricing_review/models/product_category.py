from odoo import fields, models


class ProductCategory(models.Model):
    """Add the suggested margin field to product category."""

    _inherit = "product.category"

    suggested_margin = fields.Float(
        string="Suggested Margin",
        help="Default margin if no other pricing methods are set.",
    )
