# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    def action_inventory_confirm(self):
        res = super(FSMOrder, self).action_inventory_confirm()
        for order in self:
            order.procurement_group_id.helpdesk_ticket_id = order.ticket_id
        return res

    @api.multi
    def write(self, vals):
        res = super(FSMOrder, self).write(vals)
        if 'ticket_id' in vals:
            for line in self.stock_request_ids:
                if line.state in ('draft', 'cancelled'):
                    line.ticket_id = vals.get('ticket_id')
        return res
