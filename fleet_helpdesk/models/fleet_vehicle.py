# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    helpdesk_ticket_ids = fields.One2many(
        "helpdesk.ticket", "vehicle_id", string="Tickets"
    )
    ticket_count = fields.Integer(compute="_compute_ticket_count")

    def _compute_ticket_count(self):
        Ticket = self.env["helpdesk.ticket"]
        for record in self:
            record.ticket_count = Ticket.search_count([("vehicle_id", "=", record.id)])

    def open_fleet_helpdesk(self):
        self.ensure_one()
        view = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "helpdesk.ticket",
            "name": "Tickets",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "search_default_vehicle_id": self.id,
                "default_vehicle_id": self.id,
            },
        }
        return view
