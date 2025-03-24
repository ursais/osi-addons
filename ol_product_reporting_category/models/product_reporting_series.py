# Import Odoo libs
from odoo import fields, models


class ProductReportingSeries(models.Model):
    """Add object for product reporting series."""

    _name = "product.reporting.series"
    _description = "Product Reporting Series"

    # COLUMNS ###

    name = fields.Char(
        string="Name",
        required=True,
    )
    line_id = fields.Many2one(
        "product.reporting.line",
        string="Line",
    )
    system_ids = fields.One2many(
        comodel_name="product.reporting.system",
        inverse_name="series_id",
        string="Systems",
    )

    # END #######
