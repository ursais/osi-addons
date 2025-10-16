from odoo import fields, models


class ScrapReasonCode(models.Model):
    _inherit = "scrap.reason.code"
    """Inherit scrap reason code to add company functionality."""

    # COLUMNS #####

    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    # END #########
