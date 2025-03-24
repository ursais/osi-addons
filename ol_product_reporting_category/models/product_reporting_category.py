# Import Odoo libs
from odoo import fields, models


class ProductReportingCategory(models.Model):
    """Add object for product reporting categories."""

    _name = "product.reporting.category"
    _description = "Product Reporting Category"

    # COLUMNS ###

    name = fields.Char(
        string="Name",
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="product.reporting.line",
        inverse_name="category_id",
        string="Lines",
    )

    # END #######
