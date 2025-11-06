# Import Odoo Libs
from odoo import fields, models


class ResCompany(models.Model):
    """
    Add a field for mapping a company to a user to avoid Administrator issues.
    """

    _inherit = "res.company"

    # COLUMNS #####

    external_display_name = fields.Char(string="Company Name for External Documents")
    company_user_id = fields.Many2one(
        string="Company Administrator",
        comodel_name="res.users",
    )
    short_name = fields.Char(string="Abbreviated Company Identifier")

    # END #########

    def get_all(self):
        """
        Get all companies that have a short name
        """
        return self.env["res.company"].sudo().search([("short_name", "!=", False)])
