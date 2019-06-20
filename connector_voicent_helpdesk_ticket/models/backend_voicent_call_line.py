# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class BackendVoicentCallLine(models.Model):
    _inherit = 'backend.voicent.call.line'

    applies_on = fields.Selection(
        selection_add=[('helpdesk.ticket', 'Helpdesk Ticket')])
    helpdesk_ticket_stage_id = fields.Many2one(
        'helpdesk.stage',
        string='Helpdesk Ticket Stage')
    has_parent = fields.Boolean(
        string='Must Have a Parent',
        help="""Determine if the call is made based on whether the parent of
        the ticket is set or not""")
