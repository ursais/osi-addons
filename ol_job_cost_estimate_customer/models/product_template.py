# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Inherit Product Template for adding fields.
    """

    _inherit = "product.template"

    # COLUMNS ##########

    estimate_id = fields.Many2one(
        comodel_name="sale.estimate.job",
        string="Estimate",
    )

    # END #########
