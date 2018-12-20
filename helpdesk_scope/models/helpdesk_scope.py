# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskScope(models.Model):
    _name = 'helpdesk.scope'
    _description = 'Helpdesk Scope'

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
