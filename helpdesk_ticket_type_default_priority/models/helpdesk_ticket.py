# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.onchange('ticket_type_id')
    def _onchange_ticket_type_id(self):
        if self.ticket_type_id:
            self.priority = self.ticket_type_id.default_priority
        else:
            self.priority = False
