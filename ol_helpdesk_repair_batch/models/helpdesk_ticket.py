# Import Odoo libs
from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    # COLUMNS ###

    repair_batch_ids = fields.One2many(
        comodel_name="repair.batch",
        inverse_name="ticket_id",
        string="Repair Batch",
    )

    # END #######
    # METHODS ###

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            team_id = vals.get("team_id")
            if team_id:
                team = self.env["helpdesk.team"].browse(team_id)
                if team.sequence_id:
                    vals["name"] = team.sequence_id.next_by_id()
        return super().create(vals_list)

    # END #######
