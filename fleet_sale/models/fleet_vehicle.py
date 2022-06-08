# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    sale_order_ids = fields.One2many("sale.order", "vehicle_id", string="Sale Order")
    vehicle_sale_count = fields.Integer(compute="_compute_vehicle_sale_count")

    def _compute_vehicle_sale_count(self):
        SaleOrder = self.env["sale.order"]
        for record in self:
            record.vehicle_sale_count = SaleOrder.search_count(
                [("vehicle_id", "=", record.id)]
            )

    def open_fleet_so(self):
        self.ensure_one()
        view = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "name": "Sale Order",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {
                "search_default_vehicle_id": self.id,
                "default_vehicle_id": self.id,
            },
        }
        return view
