# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    scope_id = fields.Many2one('helpdesk.scope', string="Scope")

    @api.onchange('team_id')
    def onchange_team_id(self):
        if self.team_id not in self.scope_id.team_ids:
            self.scope_id = False
