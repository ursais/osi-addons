# Import Odoo libs
from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    # COLUMNS ###

    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Ticket Sequence",
        help="If set, tickets under this team will use this sequence for naming.",
    )

    # END #######
