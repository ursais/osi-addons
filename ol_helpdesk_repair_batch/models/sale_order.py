# Import Odoo libs
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # COLUMNS ###

    helpdesk_ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Helpdesk Ticket",
    )

    # END #######
