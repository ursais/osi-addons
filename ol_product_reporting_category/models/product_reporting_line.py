# Import Odoo libs
from odoo import fields, models


class ProductReportingLine(models.Model):
    """Add object for product reporting line."""

    _name = "product.reporting.line"
    _description = "Product Reporting Line"

    # COLUMNS ###

    name = fields.Char(
        string="Name",
        required=True,
    )
    category_id = fields.Many2one(
        comodel_name="product.reporting.category",
        string="Category",
    )
    series_ids = fields.One2many(
        comodel_name="product.reporting.series",
        inverse_name="line_id",
        string="Series",
    )

    # END #######
