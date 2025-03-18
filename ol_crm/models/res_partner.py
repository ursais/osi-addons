# Import Odoo libs
from odoo import fields, models


class ResPartner(models.Model):
    """Add tag_ids field to CRM Stage."""

    _inherit = "res.partner"

    hubspot_url = fields.Char("HubSpot URL")