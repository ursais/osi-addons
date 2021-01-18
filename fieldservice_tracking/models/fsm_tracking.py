# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class FsmTracking(models.Model):
    _name = 'fsm.tracking'
    _description = 'Fsm Tracking'

    partner_id = fields.Many2one('fsm.person')
    order_id = fields.Many2one('fsm.order')
    latitude = fields.Float('Latitude')
    longitude = fields.Float('Longitude')
    # shape = fields.Char('Shape')
    timestamp = fields.Datetime()
    accuracy = fields.Float('Accuracy Radius')
    route_stage = fields.Char('Route stage')
    last_loc_age = fields.Integer('Time in seconds from last known tracking')
    substatus = fields.Char('Order Substatus')
