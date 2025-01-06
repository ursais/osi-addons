# Import Odoo libs
from odoo import fields, models


class SaleEstimateJob(models.Model):
    """Add the opportunity field to estimate."""

    _inherit = "sale.blanket.order"

    # COLUMNS ######

    opportunity_id = fields.Many2one("crm.lead")

    # END ##########
