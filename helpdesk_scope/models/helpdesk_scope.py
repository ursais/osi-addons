# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskScope(models.Model):
    _name = 'helpdesk.scope'
    _order = 'sequence'
    _description = 'Helpdesk Scope'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(required=True, default=lambda self: self.env[
        "ir.sequence"].next_by_code("helpdesk.scope") or 0)
    team_ids = fields.Many2many('helpdesk.team', string="Teams")
    active = fields.Boolean('Active', default=True)
