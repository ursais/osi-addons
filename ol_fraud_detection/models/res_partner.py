# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """Add firstname/lastname fields to partner."""

    _inherit = "res.partner"

    # COLUMNS ######

    firstname = fields.Char(string="First name", index=True)
    lastname = fields.Char(string="Last name", index=True)

    # END ##########
