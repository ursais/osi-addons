# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


REQUEST_STATES = [
    ('draft', 'Draft'),
    ('submitted', 'Submitted'),
    ('open', 'In progress'),
    ('done', 'Done'),
    ('cancel', 'Cancelled')]


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search(
            [('company_id', '=', company)], limit=1)
        return warehouse_ids

    inventory_location_id = fields.Many2one(
        'stock.location', 'Destination Location')
    stock_request_ids = fields.One2many('stock.request', 'helpdesk_ticket_id',
                                        string="Materials")
    picking_ids = fields.One2many('stock.picking', 'helpdesk_ticket_id',
                                  string='Transfers')
    delivery_count = fields.Integer(string='Delivery Orders',
                                    compute='_compute_picking_ids')
    procurement_group_id = fields.Many2one(
        'procurement.group', 'Procurement Group', copy=False)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True,
                                   default=_default_warehouse_id,
                                   help="Warehouse used to ship the materials")
    request_stage = fields.Selection(REQUEST_STATES, string='Request State',
                                     default='draft', required=True,
                                     readonly=True, store=True)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for ticket in self:
            ticket.delivery_count = len(ticket.picking_ids)

    def action_request_submit(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please create a stock request.'))
            for line in rec.stock_request_ids:
                if line.state == 'draft':
                    if line.order_id:
                        line.order_id.action_confirm()
                    else:
                        line.action_confirm()
            rec.request_stage = 'submitted'

    def action_request_cancel(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please select a Materials.'))
            for line in rec.stock_request_ids:
                if line.state in ('draft', 'submitted'):
                    if line.order_id:
                        line.order_id.action_cancel()
                    else:
                        line.action_cancel()
            rec.request_stage = 'cancel'

    def action_request_draft(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please select a Materials.'))
            for line in rec.stock_request_ids:
                if line.state == 'cancel':
                    if line.order_id:
                        line.order_id.action_draft()
                    else:
                        line.action_draft()
            rec.request_stage = 'draft'

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
