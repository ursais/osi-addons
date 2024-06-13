# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Add tariff field to product templates
    """

    _inherit = "product.template"

    # COLUMNS #####
    tariff_percent = fields.Float(
        string="Tariff Percent",
        company_dependent=True,
        help="Percentage markup of cost to include tariffs.",
    )
    # END #########
