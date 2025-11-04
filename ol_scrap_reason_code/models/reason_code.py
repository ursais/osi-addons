# Import Odoo libs
from odoo import fields, models


class ScrapReasonCode(models.Model):
    """Inherit scrap reason code to add company support."""

    _inherit = "scrap.reason.code"

    # COLUMNS #####

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
        required=True,
    )

    # END #########
