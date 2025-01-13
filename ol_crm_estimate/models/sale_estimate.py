# Import Odoo libs
from odoo import fields, models


class SaleEstimateJob(models.Model):
    """Add crm related fields."""

    _inherit = "sale.estimate.job"

    # COLUMNS ######

    opportunity_id = fields.Many2one(
        "crm.lead",
        string="Opportunity",
    )

    # END ##########
