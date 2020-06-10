# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FSMStage(models.Model):
    _inherit = 'fsm.stage'

    is_display_on_mobile = fields.Boolean('Is Display on Mobile?')
    automation_action_id = fields.Many2one(
        'base.automation', 'Automation Actions')
