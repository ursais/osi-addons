# Import Odoo libs
from odoo import models


class ResPartner(models.Model):
    """
    Add UUID compatibility
    """

    _name = "res.partner"
    _inherit = ["res.partner", "res.uuid"]
