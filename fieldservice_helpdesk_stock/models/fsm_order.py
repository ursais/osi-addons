# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class FSMOrder(models.Model):
    _inherit = 'fsm.order'

    @api.multi
    def action_request_confirm(self):
        res = super(FSMOrder, self).action_request_confirm()
        for order in self:
            if order.ticket_id:
                order.ticket_id.request_stage = order.request_stage
        return res

    @api.multi
    def write(self, vals):
        res = super(FSMOrder, self).write(vals)
        if 'ticket_id' in vals:
            for line in self.stock_request_ids:
                if line.state in ('draft', 'cancelled'):
                    line.ticket_id = vals.get('ticket_id')
        return res

    @api.onchange('location_id')
    def onchange_location_id(self):
        res = super().onchange_location_id()
        if self.location_id:
            self.warehouse_id = self.location_id.default_warehouse_id
        return res
