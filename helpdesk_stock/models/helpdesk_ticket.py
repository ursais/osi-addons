# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


REQUEST_STATES = [
    ('draft', 'Draft'),
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

    stock_request_ids = fields.One2many('stock.request', 'ticket_id',
                                        string="Materials")
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
    request_stage = fields.Selection(REQUEST_STATES, string='Request State',
                                     default='draft', required=True,
                                     readonly=True, store=True)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for ticket in self:
            ticket.delivery_count = len(ticket.picking_ids)

    @api.multi
    def action_confirm(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please select a Materials.'))
            group_id = rec.procurement_group_id or False
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': rec.name,
                    'move_type': 'direct',
                    'helpdesk_ticket_id': rec.id,
                    'partner_id': rec.partner_id.id,
                })
                rec.procurement_group_id = group_id.id
            for line in rec.stock_request_ids:
                line.procurement_group_id = group_id.id
                line.action_confirm()
            rec.request_stage = 'open'

    def action_cancel(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please select a Materials.'))
            for line in rec.stock_request_ids:
                line.action_cancel()
            rec.request_stage = 'cancel'

    @api.multi
    def action_draft(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please select a Materials.'))
            for line in rec.stock_request_ids:
                line.action_draft()
            rec.request_stage = 'draft'

    @api.multi
    def action_done(self):
        for rec in self:
            if not rec.stock_request_ids:
                raise UserError(_('Please select a Materials.'))
            for line in rec.stock_request_ids:
                line.action_done()
            rec.request_stage = 'done'

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
