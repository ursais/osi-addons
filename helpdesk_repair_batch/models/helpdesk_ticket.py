# Import Odoo libs
from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    # COLUMNS ###

    repair_batch_ids = fields.One2many(
        comodel_name="repair.batch",
        inverse_name="ticket_id",
        string="Repair Batch",
    )

    # END #######
