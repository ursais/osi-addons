# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    @api.onchange('direction', 'fsm_order_id', 'helpdesk_ticket_id')
    def _onchange_location_id(self):
        super()._onchange_location_id()
        # FSM Order takes priority over Helpdesk Ticket
        if self.fsm_order_id:
            if self.direction == 'outbound':
                # Inventory location of the FSM location of the order
                self.location_id = \
                    self.fsm_order_id.location_id.inventory_location_id.id
            else:
                # Otherwise the stock location of the warehouse
                self.location_id = \
                    self.fsm_order_id.warehouse_id.lot_stock_id.id

    @api.model
    def create(self, vals):
        if 'fsm_order_id' in vals and vals['fsm_order_id']:
            order = self.env['fsm.order'].browse(vals['fsm_order_id'])
            if order.ticket_id:
                vals.update({
                    'helpdesk_ticket_id': order.ticket_id.id or False})
        return super().create(vals)

    @api.multi
    def write(self, vals):
        if 'fsm_order_id' in vals and vals['fsm_order_id']:
            order = self.env['fsm.order'].browse(vals['fsm_order_id'])
            vals.update({'helpdesk_ticket_id': order.ticket_id.id or False})
        return super().write(vals)

    def prepare_order_values(self, vals):
        res = super().prepare_order_values(vals)
        if 'fsm_order_id' in vals and vals['fsm_order_id']:
            fsm_order = self.env['fsm.order'].browse(vals['fsm_order_id'])
            res.update({
                'fsm_order_id': vals['fsm_order_id'],
                'helpdesk_ticket_id': fsm_order.ticket_id.id or False,
            })
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        if self.helpdesk_ticket_id:
            res.update({
                'helpdesk_ticket_id': self.helpdesk_ticket_id.id,
                'partner_id':
                    self.helpdesk_ticket_id.fsm_location_id.partner_id.id,
            })
        if self.fsm_order_id:
            res.update({
                'fsm_order_id': self.fsm_order_id.id,
                'helpdesk_ticket_id': self.fsm_order_id.ticket_id.id or False,
                'partner_id': self.fsm_order_id.location_id.partner_id.id,
            })
        return res

    def _prepare_procurement_group_values(self):
        res = super()._prepare_procurement_group_values()
        if self.fsm_order_id:
            res.update({'name': self.fsm_order_id.name,
                        'fsm_order_id': self.fsm_order_id.id,
                        'helpdesk_ticket_id':
                            self.fsm_order_id.ticket_id.id or False})
        return res
