# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.onchange("team_id")
    def _onchange_ticket_type_id(self):
        self.ticket_type_id = False
        if not self.team_id or not self.team_id.ticket_type_ids:
            return {"domain": {"ticket_type_id": [("team_id", "=", False)]}}
        else:
            ticket_types = self.env["helpdesk.ticket.type"].search(
                [("team_id", "=", self.team_id.id)]
            )
            if len(ticket_types) == 1:
                self.ticket_type_id = ticket_types[0].id
                return {
                    "domain": {"ticket_type_id": [("team_id", "=", self.team_id.id)]}
                }
            elif len(ticket_types) > 1:
                return {
                    "domain": {"ticket_type_id": [("team_id", "=", self.team_id.id)]}
                }
