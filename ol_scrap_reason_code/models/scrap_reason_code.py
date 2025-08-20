from odoo import fields, models


class ScrapReasonCode(models.Model):
    _inherit = "scrap.reason.code"
    """Inherit scrap resaon code to add compnay functionality."""

    # COLUMNS #####

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    # END #########
