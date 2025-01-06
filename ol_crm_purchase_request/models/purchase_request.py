# Import Odoo libs
from odoo import fields, models


class PurchaseRequest(models.Model):
    """Add a opportunity field to Purchase Requests."""

    _inherit = "purchase.request"

    # COLUMNS ######

    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")

    # END ##########
