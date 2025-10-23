# Import Odoo libs
from odoo import api, fields, models


class StockPicking(models.Model):
    """Inherit stock picking to add ticket relationship."""

    _inherit = "stock.picking"

    # COLUMNS ###

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Ticket",
    )

    # END #######
