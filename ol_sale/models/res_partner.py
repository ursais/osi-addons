# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """Add new field to Partners."""

    _inherit = "res.partner"

    # COLUMNS #####

    account_manager_id = fields.Many2one(
        "res.users",
        string="Account Manager",
    )

    # END #########
