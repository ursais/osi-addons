# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'
    _description = 'Helpdesk Team'

    use_scope = fields.Boolean('Scopes')
    scope_ids = fields.Many2many('helpdesk.scope', string="Scopes")
