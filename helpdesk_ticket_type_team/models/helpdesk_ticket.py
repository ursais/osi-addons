# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    @api.onchange("team_id")
    def _onchange_team_id(self):
        self.ticket_type_id = False
        self.user_id = False
        if not self.team_id or not self.team_id.ticket_type_ids:
            return {"domain": {"ticket_type_id": [("team_id", "=", False)]}}
        else:
            return {
                "domain": {
                    "ticket_type_id": [("team_id", "=", self.team_id.id)],
                    "user_id": [("team_ids", "=", self.team_id.id)],
                }
            }
