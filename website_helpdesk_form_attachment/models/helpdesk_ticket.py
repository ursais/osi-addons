# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields

TICKET_SEVERITY = [
    ('0', 'Informational'),
    ('1', 'Minor'),
    ('2', 'Significant'),
    ('3', 'Critical'),
]


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    severity = fields.Selection(TICKET_SEVERITY, string='Severity',
                                default='0')
