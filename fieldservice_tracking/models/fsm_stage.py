# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class FSMStage(models.Model):
    _inherit = "fsm.stage"

    start_tracking = fields.Boolean()
    stop_tracking = fields.Boolean()
    notify_customer = fields.Boolean()
    notify_dispatcher = fields.Boolean()
    distance_to_next_stop = fields.Boolean("Compare Distance to next stop")
