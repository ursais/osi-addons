# Import Odoo Libs
from odoo import fields, models


class ResCompany(models.Model):
    """
    Add a field for mapping a company to a user to avoid Administrator issues.
    """

    _inherit = "res.company"

    # COLUMNS #####

    company_user_id = fields.Many2one(
        string="Company Administrator",
        comodel_name="res.users",
    )

    # END #########
