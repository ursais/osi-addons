# Import Odoo libs
from odoo import fields, models


class CRMLead(models.Model):
    """Add quantity field to Leads."""

    _inherit = "crm.lead"

    # COLUMNS ######

    quantity = fields.Integer(string="Expected Volume")

    # END ##########
