# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        copy=False,
    )
