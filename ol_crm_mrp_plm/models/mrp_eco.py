# Import Odoo libs
from odoo import fields, models


class MrpEco(models.Model):
    """Add opportunity field on Engineering Change Orders."""

    _inherit = "mrp.eco"

    # COLUMNS ######

    opportunity_id = fields.Many2one(
        "crm.lead",
        string="Opportunity",
    )

    # END ##########
