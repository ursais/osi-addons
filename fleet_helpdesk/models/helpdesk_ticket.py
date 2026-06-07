# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicket(models.Model):
    """Extends helpdesk.ticket to add fleet vehicle integration.

    This model adds the ability to link a fleet vehicle to a helpdesk ticket,
    enabling support teams to track vehicle-related issues and maintenance
    requests through the helpdesk system.
    """

    _inherit = "helpdesk.ticket"

    # Relational Fields
    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string="Vehicle",
        copy=False,
        help="The fleet vehicle associated with this helpdesk ticket. "
        "Use this to link vehicle maintenance or issue requests to tickets.",
    )
