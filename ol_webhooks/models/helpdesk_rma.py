# Import Python libs

# Import Odoo libs
from odoo import models


class HelpdeskRma(models.Model):
    """
    Add webhook compatibility to RMAs
    """

    _name = "helpdesk.rma"
    _inherit = ["helpdesk.rma", "webhook.mixin"]
