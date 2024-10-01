# Import Odoo libs
from odoo import fields, models


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    # COLUMNS ######

    estimate_id = fields.Many2one(
        "sale.estimate.job",
        string="Sale Estimate",
    )

    # END ##########
