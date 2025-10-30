# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FleetVehicle(models.Model):
    """Extends fleet.vehicle to add helpdesk ticket integration.
    
    This model adds the ability to link helpdesk tickets to fleet vehicles,
    providing a direct relationship between vehicle maintenance/issues and
    helpdesk support tickets.
    """
    
    _inherit = "fleet.vehicle"

    # Relational Fields
    helpdesk_ticket_ids = fields.One2many(
        comodel_name="helpdesk.ticket",
        inverse_name="vehicle_id",
        string="Tickets",
        help="List of all helpdesk tickets associated with this vehicle"
    )
    
    # Computed Fields
    ticket_count = fields.Integer(
        compute="_compute_ticket_count",
        string="Ticket Count",
        help="Total number of helpdesk tickets for this vehicle"
    )

    @api.depends("helpdesk_ticket_ids")
    def _compute_ticket_count(self):
        """Compute the total count of helpdesk tickets for each vehicle.
        
        This method counts all helpdesk tickets associated with the current
        vehicle record. The count is used to display a smart button in the
        vehicle form view.
        """
        for record in self:
            record.ticket_count = len(record.helpdesk_ticket_ids)

    def open_fleet_helpdesk(self):
        """Open a view showing all helpdesk tickets for this vehicle.
        
        This action method is called from the smart button on the vehicle form.
        It opens a filtered view showing only the helpdesk tickets related to
        the current vehicle, with the vehicle pre-selected in the context for
        creating new tickets.
        
        Returns:
            dict: Action dictionary to open the helpdesk ticket list/form view
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "helpdesk.ticket",
            "name": "Tickets",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "search_default_vehicle_id": self.id,
                "default_vehicle_id": self.id,
            },
        }
