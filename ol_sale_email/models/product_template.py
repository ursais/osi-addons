# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Add allow_backorder field Product Template
    """

    _inherit = "product.template"

    # COLUMNS #####

    allow_backorder = fields.Boolean(default=True, company_dependent=True)

    # END #########
