# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    fsm_location_id = fields.Many2one('fsm.location', string="FSM Location")

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
        if self.fsm_order_id.location_id:
                self.fsm_location_id = self.fsm_order_id.location_id

    @api.model
    def create(self, vals):
        if 'fsm_order_id' in vals and vals['fsm_order_id']:
            order = self.env['fsm.order'].browse(vals['fsm_order_id'])
            if order.ticket_id:
                vals.update({
                    'helpdesk_ticket_id': order.ticket_id.id or False})
            vals.update({
                'fsm_location_id': order.location_id.id or False
            })
        elif vals.get('helpdesk_ticket_id', False):
            ticket = self.env['helpdesk.ticket'].\
                browse(vals['helpdesk_ticket_id'])
            vals.update({
                'fsm_location_id': ticket.fsm_location_id.id or False})
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
                'fsm_location_id': fsm_order.location_id.id
            })
        return res

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        if self.helpdesk_ticket_id:
            res.update({
                'helpdesk_ticket_id': self.helpdesk_ticket_id.id,
                'partner_id':
                    self.helpdesk_ticket_id.fsm_location_id.
                    shipping_address_id.id or
                    self.helpdesk_ticket_id.fsm_location_id.partner_id.id
            })
        if self.fsm_order_id:
            res.update({
                'fsm_order_id': self.fsm_order_id.id,
                'helpdesk_ticket_id': self.fsm_order_id.ticket_id.id or False,
                'partner_id':
                    self.fsm_order_id.location_id.
                    shipping_address_id.id or
                    self.fsm_order_id.location_id.partner_id.id
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

    @api.multi
    def _action_confirm(self):
        for req in self:
            # If we can find a group, use it
            if (req.procurement_group_id) or \
                    (req.order_id and req.order_id.procurement_group_id):
                req.procurement_group_id = \
                    req.procurement_group_id.id or \
                    (req.order_id and req.order_id.procurement_group_id.id)
                res = super(StockRequest, req)._action_confirm()
            # otherwise create one with the fsm order if we have one
            elif req.fsm_order_id:
                fsm_order = self.env['fsm.order'].browse(req.fsm_order_id.id)
                group = self.env['procurement.group'].search([
                    ('fsm_order_id', '=', fsm_order.id)])
                if not group:
                    values = req._prepare_procurement_group_values()
                    group = self.env['procurement.group'].create(values)
                if req.order_id:
                    req.order_id.procurement_group_id = group.id
                req.procurement_group_id = group.id
                res = super(StockRequest, req)._action_confirm()
                fsm_order.request_stage = 'open'
            # otherwise create one with the ticket if we have one
            elif req.helpdesk_ticket_id:
                ticket = self.env['helpdesk.ticket'].browse(
                    req.helpdesk_ticket_id.id)
                # If the ticket has many fsm orders, use the group with no
                # fsm_order_id
                group = self.env['procurement.group'].search([
                    ('helpdesk_ticket_id', '=', ticket.id),
                    ('fsm_order_id', '=', False)])
                if not group:
                    values = req._prepare_procurement_group_values()
                    group = self.env['procurement.group'].create(values)
                if req.order_id:
                    req.order_id.procurement_group_id = group.id
                req.procurement_group_id = group.id
                res = super(StockRequest, req)._action_confirm()
                ticket.request_stage = 'open'
            else:
                res = super(StockRequest, req)._action_confirm()
        return res
