# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    gvwr_kg = fields.Integer(index=True)
    gvwr_lbs = fields.Integer(index=True)
    gawr_front_kg = fields.Integer(index=True)
    gawr_front_lbs = fields.Integer(index=True)
    gawr_rear_kg = fields.Integer(index=True)
    gawr_rear_lbs = fields.Integer(index=True)
    front_cold_tier_pressure_kpa = fields.Integer(index=True)
    front_cold_tier_pressure_psi = fields.Integer(index=True)
    rear_cold_tier_pressure_kpa = fields.Integer(index=True)
    rear_cold_tier_pressure_psi = fields.Integer(index=True)
    front_tier_size = fields.Char(index=True)
    rear_tier_size = fields.Char(index=True)
    front_rim = fields.Char(index=True)
    rear_rim = fields.Char(index=True)
    vehicle_certification = fields.Selection([("Complete", "Complete"),
                                              ("Incomplete", "Incomplete")])
