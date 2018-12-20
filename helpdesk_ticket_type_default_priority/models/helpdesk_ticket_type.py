# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    default_priority = fields.Selection([('0', 'All'),
                                         ('1', 'Low Priority'),
                                         ('2', 'High Priority'),
                                         ('3', 'Urgent')],
                                        string="Default Priority")
