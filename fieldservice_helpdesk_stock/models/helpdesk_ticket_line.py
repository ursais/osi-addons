# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTicketLine(models.Model):
    _inherit = 'helpdesk.ticket.line'

    fsm_order_line_id = fields.Many2one('fsm.order.line',
                                        string='Field Service Order Line')
