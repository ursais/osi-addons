# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class FsmPerson(models.Model):
    _inherit = 'fsm.person'

    track_lat = fields.Float('Last known latitude')
    track_long = fields.Float('Last known longitude')
    # track_shape = fields.Char('Last known location')
    loc_rad = fields.Float('Last known location accuracy radius')
    loc_time = fields.Datetime('Last location ping')
    rad_uom = fields.Many2one('uom.uom', 'Unit of measure')

    # only visible to dispatchers
    match_rad = fields.Integer('Max allowed distance')
    track_intv_coarse = fields.Integer('Time in seconds')
    fence_rad = fields.Integer('Distance from destination')
    route_stage = fields.Selection([
        ('out', 'Out'), ('checkin', 'Check-in'), ('enroute', 'Enroute'), ('jobstart', 'Job Start'),
        ('working', 'Working'), ('jobstop', 'Job Stop'), ('checkout', 'Check-out'), ('break', 'Break')
    ], string='Route Stage')
