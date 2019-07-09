# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockRequest(models.Model):
    _inherit = 'stock.request'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string="Ticket",
                                         ondelete='cascade', index=True,
                                         copy=False)

    @api.onchange('direction', 'helpdesk_ticket_id')
    def _onchange_location_id(self):
        super()._onchange_location_id()
        if self.helpdesk_ticket_id:
            if self.direction == 'outbound':
                # Inventory location of the ticket
                self.location_id = \
                    self.helpdesk_ticket_id.inventory_location_id.id
            else:
                # Otherwise the stock location of the warehouse
                self.location_id = \
                    self.helpdesk_ticket_id.warehouse_id.lot_stock_id.id

    def prepare_order_values(self, vals):
        res = {
            'expected_date': vals['expected_date'],
            'picking_policy': vals['picking_policy'],
            'warehouse_id': vals['warehouse_id'],
            'direction': vals['direction'],
            'location_id': vals['location_id'],
        }
        if 'helpdesk_ticket_id' in vals and vals['helpdesk_ticket_id']:
            res.update({'helpdesk_ticket_id': vals['helpdesk_ticket_id']})
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'helpdesk_ticket_id' in vals and vals['helpdesk_ticket_id']:
            ticket = self.env['helpdesk.ticket'].browse(
                vals['helpdesk_ticket_id'])
            ticket.request_stage = 'draft'
            order = self.env['stock.request.order'].search([
                ('helpdesk_ticket_id', '=', vals['helpdesk_ticket_id']),
                ('direction', '=', vals['direction']),
                ('date_expected', '=', vals['date_expected']),
                ('state', '=', 'draft')
            ])
            if order:
                res.order_id = order.id
            else:
                values = self.prepare_order_values(vals)
                res.order_id = self.env['stock.request.order'].create(values)
        return res

    def _prepare_procurement_group_values(self):
        if self.helpdesk_ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(
                self.helpdesk_ticket_id.id)
            return {'name': ticket.name,
                    'fsm_order_id': ticket.id,
                    'move_type': 'direct'}
        else:
            return {}

    def _prepare_procurement_values(self, group_id=False):
        res = super()._prepare_procurement_values(group_id=group_id)
        res.update({
            'helpdesk_ticket_id': self.helpdesk_ticket_id.id,
            'partner_id': self.helpdesk_ticket_id.partner_id.id,
        })
        return res

    @api.multi
    def _action_confirm(self):
        if self.helpdesk_ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(
                self.helpdesk_ticket_id.id)
            group = self.env['procurement.group'].search([
                ('helpdesk_ticket_id', '=', ticket.id)])
            if not group:
                values = self._prepare_procurement_group_values()
                group = self.env['procurement.group'].create(values)
            if self.order_id:
                self.order_id.procurement_group_id = group.id
            self.procurement_group_id = group.id
            res = super()._action_confirm()
            ticket.request_stage = 'open'
        else:
            res = super()._action_confirm()
        return res
