# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """Inherit product template for product reporting categories."""

    _inherit = "product.template"

    # COLUMNS ###

    reporting_system_id = fields.Many2one(
        comodel_name="product.reporting.system",
        string="Reporting Category",
    )

    # END #######
