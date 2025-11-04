# Import Odoo libs
from odoo import fields, models


class AccountMove(models.Model):
    """Inherit Account Move for field changes."""

    _inherit = "account.move"

    # COLUMNS #####

    helpdesk_ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Helpdesk Ticket",
    )

    # END #########
