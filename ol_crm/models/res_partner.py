# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """Add hotspot url field to partner."""

    _inherit = "res.partner"

    # COLUMNS ######

    hubspot_url = fields.Char("HubSpot URL")
    firstname = fields.Char(string="First name", index=True)
    lastname = fields.Char(string="Last name", index=True)

    # END ##########
