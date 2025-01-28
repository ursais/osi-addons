# Import Odoo libs
from odoo import fields, models


class MRPEco(models.Model):
    """
    Inherit MRP Eco for adding fields.
    """

    _inherit = "mrp.eco"

    # COLUMNS ##########

    estimate_id = fields.Many2one(
        comodel_name="sale.estimate.job",
        string="Estimate",
    )

    # END #########
