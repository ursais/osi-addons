# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    scope_id = fields.Many2many('helpdesk.scope', string="Scopes")
