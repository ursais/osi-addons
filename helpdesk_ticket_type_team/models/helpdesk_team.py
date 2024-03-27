# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    ticket_type_ids = fields.One2many(
        "helpdesk.ticket.type", "team_id", string="Assigned ticket types"
    )
