# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

STOCK_STAGES = [('draft', 'Draft'),
                ('requested', 'Requested'),
                ('confirmed', 'Confirmed'),
                ('partial', 'Partially Shipped'),
                ('done', 'Done'),
                ('cancelled', 'Cancelled')]


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search(
            [('company_id', '=', company)], limit=1)
        return warehouse_ids

    inventory_location_id = fields.Many2one('stock.location',
                                            'Destination Location')
    line_ids = fields.One2many(
        'helpdesk.ticket.line', 'ticket_id', string="Materials",)
    picking_ids = fields.One2many('stock.picking', 'helpdesk_ticket_id',
                                  string='Transfers')
    delivery_count = fields.Integer(string='Delivery Orders',
                                    compute='_compute_picking_ids')
    procurement_group_id = fields.Many2one(
        'procurement.group', 'Procurement Group', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True, readonly=True,
                                   default=_default_warehouse_id,
                                   help="Warehouse used to ship the materials")
    inventory_stage = fields.Selection(STOCK_STAGES, string='State',
                                       default='draft', required=True,
                                       readonly=True, store=True)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for ticket in self:
            ticket.delivery_count = len(ticket.picking_ids)

    def action_inventory_request(self):
        if self.fsm_location_id and self.line_ids:
            for line in self.line_ids:
                if line.state == 'draft':
                    line.state = 'requested'
                    line.qty_ordered = line.qty_requested
            self.inventory_stage = 'requested'
        else:
            raise UserError(_('Please select a location and a product.'))

    def action_inventory_confirm(self):
        if self.line_ids and self.warehouse_id and self.inventory_location_id:
            self.line_ids._confirm_picking()
            self.inventory_stage = 'confirmed'
            return True
        else:
            raise UserError(_('Please select the location, a warehouse and a'
                              ' product.'))

    def action_inventory_cancel(self):
        for line in self.line_ids:
            if line.state == 'requested':
                line.state = 'cancelled'
            self.inventory_stage = 'cancelled'

    def action_inventory_reset(self):
        for line in self.line_ids:
            if line.state == 'cancelled':
                line.state = 'draft'
        self.inventory_stage = 'draft'

    @api.multi
    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given helpdesk ticket ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('stock.action_picking_tree_all').read()[0]

        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('stock.view_picking_form').id,
                                'form')]
            action['res_id'] = pickings.id
        return action
