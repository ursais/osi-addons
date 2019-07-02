# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    @api.model
    def create(self, vals):
        if 'helpdesk_ticket_id' in vals and vals['helpdesk_ticket_id']:
            ticket = self.env['helpdesk.ticket'].browse(
                vals['helpdesk_ticket_id'])
            vals.pop('helpdesk_ticket_id')
            res = super().create(vals)
            res.helpdesk_ticket_id = ticket.id
            ticket.write({'request_stage': 'draft'})
        else:
            res = super().create(vals)
        return res
