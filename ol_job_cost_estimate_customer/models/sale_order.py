# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    """
    Add new fields to Sale Order
    """

    _inherit = "sale.order"

    # COLUMNS #####

    estimate_id = fields.Many2one(
        "sale.estimate.job",
        string="Estimate",
    )

    # END #########
