# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket')
