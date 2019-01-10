# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FSMOrderLine(models.Model):
    _inherit = 'fsm.order.line'

    helpdesk_ticket_line_id = fields.Many2one('helpdesk.ticket.line',
                                              string='Helpdesk Ticket Line',
                                              readonly=True)

    @api.multi
    def _prepare_helpdesk_ticket_line_values(self):
        return {'product_id': self.product_id.id,
                'name': self.name,
                'qty_ordered': self.qty_ordered,
                'product_uom_id': self.product_uom_id.id,
                'route_id': self.route_id.id,
                'fsm_order_line_id': self.id,
                'ticket_id': self.order_id.ticket_id.id}

    def create(self, vals):
        res = super(FSMOrderLine, self).create(vals)
        if res.order_id.ticket_id:
            values = res._prepare_helpdesk_ticket_line_values()
            helpdesk_ticket_line = self.env['helpdesk.ticket.line'].create(
                values)
            res.update({'helpdesk_ticket_line_id': helpdesk_ticket_line.id})
        return res

    def write(self, vals):
        res = super(FSMOrderLine, self).write(vals)
        if res and self.helpdesk_ticket_line_id:
            if 'product_id' in vals:
                self.helpdesk_ticket_line_id.product_id = vals['product_id']
            if 'name' in vals:
                self.helpdesk_ticket_line_id.name = vals['name']
            if 'qty_requested' in vals:
                self.helpdesk_ticket_line_id.qty_requested = \
                    vals['qty_requested']
            if 'qty_ordered' in vals:
                self.helpdesk_ticket_line_id.qty_ordered = vals['qty_ordered']
        return res
