# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    has_stage_changed = fields.Boolean(default=False)

    @api.multi
    def write(self, vals):
        if 'stage_id' in vals:
            vals.update({'has_stage_changed': True})
        else:
            vals.update({'has_stage_changed': False})
        return super(HelpdeskTicket, self).write(vals)