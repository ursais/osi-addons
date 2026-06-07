# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FleetVehicle(models.Model):
    """
    Extends the fleet.vehicle model to add sales functionality.

    This model adds the ability to:
    - Track sale orders associated with each vehicle
    - Display a count of sale orders for each vehicle
    - Provide quick access to view related sale orders

    Note: This module is designed to be compatible with Odoo 18+.
    """

    _inherit = "fleet.vehicle"

    # One2many field to link sale orders to this vehicle
    # This field creates a relationship from vehicle to sale orders
    sale_order_ids = fields.One2many(
        "sale.order",
        "vehicle_id",
        string="Sale Orders",
        help="Sale orders associated with this vehicle",
    )

    # Computed field to count sale orders for this vehicle
    # The field is computed on-demand and not stored for performance
    vehicle_sale_count = fields.Integer(
        string="Sale Order Count",
        compute="_compute_vehicle_sale_count",
        store=False,  # Not stored as it's computed on demand
        help="Number of sale orders associated with this vehicle",
    )

    @api.depends("sale_order_ids")
    def _compute_vehicle_sale_count(self):
        """
        Compute the number of sale orders associated with each vehicle.

        This method counts all sale orders where the vehicle_id field
        matches the current vehicle's ID. The count is computed for
        each vehicle record in the recordset.

        This method is compatible with Odoo 18 and uses the modern
        compute pattern with @api.depends decorator.
        """
        SaleOrder = self.env["sale.order"]
        for record in self:
            # Count sale orders where vehicle_id matches this vehicle
            # Using search_count for efficiency
            record.vehicle_sale_count = SaleOrder.search_count(
                [("vehicle_id", "=", record.id)]
            )

    def action_open_fleet_sale_orders(self):
        """
        Open a window showing all sale orders for this vehicle.

        Returns:
            dict: Action window configuration to display sale orders
                 filtered by the current vehicle

        This method is compatible with Odoo 18 and creates a proper
        action window for viewing related sale orders.
        """
        self.ensure_one()

        # Create action window to display sale orders
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "view_id": False,
            "res_model": "sale.order",
            "name": "Sale Orders",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "search_default_vehicle_id": self.id,
                "default_vehicle_id": self.id,
            },
        }
        return action

    # Keep the old method name for backward compatibility
    def open_fleet_so(self):
        """
        Legacy method name for backward compatibility.

        This method is kept to maintain compatibility with existing
        XML views that might reference the old method name.

        This method is preserved for backward compatibility with
        older versions of the module or views that reference the
        old naming convention.
        """
        return self.action_open_fleet_sale_orders()
