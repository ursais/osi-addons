# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockRequest(models.Model):
    _inherit = "stock.request"

    ticket_id = fields.Many2one(
        'helpdesk.ticket', string="Helpdesk Ticket",
        ondelete='cascade', index=True, copy=False)

    @api.onchange('direction', 'ticket_id')
    def _onchange_fsm_location_id(self):
        if self.direction == 'outbound':
            # Inventory location of the FSM location of the order
            self.location_id = \
                self.ticket_id.fsm_location_id.inventory_location_id.id
        else:
            # Otherwise the stock location of the warehouse
            self.location_id = \
                self.ticket_id.warehouse_id.lot_stock_id.id

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'ticket_id' in vals:
            ticket_id = self.env['helpdesk.ticket'].browse(vals['ticket_id'])
            ticket_id.write({'request_stage': 'draft'})
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        res = super(StockMoveLine, self)._action_done()
        for rec in self:
            for all_rec in rec.move_id.allocation_ids:
                request = all_rec.stock_request_id
                if request.state == 'done' and request.ticket_id:
                    request.ticket_id.request_stage = 'done'
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', 'Helpdesk Ticket')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    helpdesk_ticket_id = fields.Many2one(
        related="group_id.helpdesk_ticket_id", string="Helpdesk Ticket",
        store=True)
