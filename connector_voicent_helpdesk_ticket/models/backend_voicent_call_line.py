# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BackendVoicentCallLine(models.Model):
    _inherit = 'backend.voicent.call.line'

    applies_on = fields.Selection(
        selection_add=[('helpdesk_ticket', 'Helpdesk Ticket')]
    )
    helpdesk_ticket_stage_id = fields.Many2one(
        'helpdesk.stage',
        string='Helpdesk Ticket Stage'
    )
