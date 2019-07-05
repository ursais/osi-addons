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
        if self.direction == 'outbound':
            # Inventory location of the ticket
            self.location_id = self.helpdesk_ticket_id.inventory_location_id.id
        else:
            # Otherwise the stock location of the warehouse
            self.location_id = \
                self.helpdesk_ticket_id.warehouse_id.lot_stock_id.id

    @api.model
    def create(self, vals):
        if 'helpdesk_ticket_id' in vals and vals['helpdesk_ticket_id']:
            ticket = self.env['helpdesk.ticket'].browse(
                vals['helpdesk_ticket_id'])
            group = self.env['procurement.group'].search([
                ('helpdesk_ticket_id', '=', ticket.id)])
            if not group:
                group = self.env['procurement.group'].create({
                    'name': ticket.name,
                    'helpdesk_ticket_id': ticket.id,
                    'move_type': 'direct'})
            vals.update({'procurement_group_id': group.id})
            res = super().create(vals)
            ticket.write({'request_stage': 'draft'})
        else:
            res = super().create(vals)
        return res
