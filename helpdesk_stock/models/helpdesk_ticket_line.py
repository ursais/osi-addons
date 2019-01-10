# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime, timedelta

from odoo import api, fields, models

from odoo.tools import (DEFAULT_SERVER_DATETIME_FORMAT,
                        float_is_zero, float_compare)
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

STOCK_STAGES = [('draft', 'Draft'),
                ('requested', 'Requested'),
                ('confirmed', 'Confirmed'),
                ('partial', 'Partially Shipped'),
                ('done', 'Done'),
                ('cancelled', 'Cancelled')]


class HelpdeskTicketLine(models.Model):
    _name = 'helpdesk.ticket.line'
    _description = "Helpdesk Ticket Lines"
    _order = 'ticket_id, sequence, id'

    ticket_id = fields.Many2one(
        'helpdesk.ticket', string="Helpdesk Ticket", required=True,
        ondelete='cascade', index=True, copy=False,
        readonly=True, states={'draft': [('readonly', False)]})
    name = fields.Char(string='Description', required=True,
                       readonly=True, states={'draft': [('readonly', False)]})
    sequence = fields.Integer(string='Sequence', default=10, readonly=True,
                              states={'draft': [('readonly', False)]})
    product_id = fields.Many2one(
        'product.product', string="Product",
        domain=[('type', '=', 'product')], ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]})
    product_uom_id = fields.Many2one(
        'product.uom', string='Unit of Measure', required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    qty_requested = fields.Float(
        string='Quantity Requested', readonly=True,
        states={'draft': [('readonly', False)]},
        digits=dp.get_precision('Product Unit of Measure'))
    qty_ordered = fields.Float(
        string='Quantity Ordered', readonly=True,
        states={'requested': [('readonly', False)]},
        digits=dp.get_precision('Product Unit of Measure'))
    qty_delivered = fields.Float(
        string='Quantity Delivered', readonly=True, copy=False,
        digits=dp.get_precision('Product Unit of Measure'))
    state = fields.Selection(STOCK_STAGES, string='State',
                             compute='_compute_state', copy=False, index=True,
                             readonly=True, store=True)
    move_ids = fields.One2many(
        'stock.move', 'helpdesk_ticket_line_id', string='Stock Moves',
        readonly=True, states={'draft': [('readonly', False)]})
    route_id = fields.Many2one('stock.location.route', string='Route',
                               domain=[('helpdesk_selectable', '=', True)],
                               ondelete='restrict')

    @api.depends('move_ids', 'qty_ordered', 'qty_delivered')
    def _compute_state(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for line in self:
            if line.move_ids and not float_is_zero(line.qty_delivered,
                                                   precision_digits=precision):
                if float_compare(line.qty_delivered, line.qty_ordered,
                                 precision_digits=precision) == -1:
                    line.state = 'partial'
                elif float_compare(line.qty_delivered, line.qty_ordered,
                                   precision_digits=precision) >= 0:
                    line.state = 'done'
            elif line.move_ids:
                line.state = 'confirmed'
            else:
                if line.qty_ordered != 0:
                    line.state = 'requested'
                else:
                    line.state = 'draft'

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=',
                                   self.product_id.uom_id.category_id.id)]}

        if (not self.product_uom_id
                or (self.product_id.uom_id.id != self.product_uom_id.id)):
            vals['product_uom_id'] = self.product_id.uom_id
            vals['qty_requested'] = 1.0

        product = self.product_id.with_context(
            quantity=vals.get('qty_requested') or self.qty_requested,
            uom=self.product_uom_id.id,
        )

        result = {'domain': domain}

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self.update(vals)
        return result

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        values = {}
        date_planned = ((datetime.now() + timedelta(days=1)).strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT))
        values.update({
            'group_id': group_id,
            'helpdesk_ticket_line_id': self.id,
            'date_planned': date_planned,
            'route_ids':
                self.route_id or self.ticket_id.warehouse_id.delivery_route_id,
            'partner_dest_id': self.ticket_id.partner_id
        })
        return values

    def _get_procurement_qty(self):
        self.ensure_one()
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state != 'cancel'):
            if move.picking_code == 'outgoing':
                qty += move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom_id,
                    rounding_method='HALF-UP')
            elif move.picking_code == 'incoming':
                qty -= move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom_id,
                    rounding_method='HALF-UP')
        return qty

    @api.multi
    def _confirm_picking(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        errors = []
        for line in self:
            qty_procured = line._get_procurement_qty()
            if float_compare(qty_procured, line.qty_ordered,
                             precision_digits=precision) >= 0:
                continue
            group_id = line.ticket_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.ticket_id.name,
                    'move_type': 'direct',
                    'helpdesk_ticket_id': line.ticket_id.id,
                    'partner_id': line.ticket_id.partner_id.id,
                })
                line.ticket_id.procurement_group_id = group_id
            values = line._prepare_procurement_values(group_id=group_id)
            qty_needed = line.qty_ordered - qty_procured
            procurement_uom = line.product_uom_id
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if (procurement_uom.id != quant_uom.id
                    and get_param('stock.propagate_uom') != '1'):
                qty_needed = line.product_uom_id._compute_quantity(
                    qty_needed, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom
            try:
                self.env['procurement.group'].run(
                    line.product_id, qty_needed, procurement_uom,
                    line.ticket_id.inventory_location_id,
                    line.name, line.ticket_id.name, values)
            except UserError as error:
                errors.append(error.name)
        if errors:
            raise UserError('\n'.join(errors))
        return True

    @api.multi
    def _get_delivered_qty(self):
        self.ensure_one()
        qty = 0.0
        for move in self.move_ids.filtered(lambda r: r.state == 'done'
                                           and not r.scrapped):
            if move.location_dest_id.usage == "customer":
                if (not move.origin_returned_move_id
                        or (move.origin_returned_move_id and move.to_refund)):
                    qty += move.product_uom._compute_quantity(
                        move.product_uom_qty, self.product_uom_id)
            elif (move.location_dest_id.usage != "customer"
                    and move.to_refund):
                qty -= move.product_uom._compute_quantity(
                    move.product_uom_qty, self.product_uom_id)
        return qty

    def create(self, vals):
        res = super(HelpdeskTicketLine, self).create(vals)
        if 'ticket_id' in vals:
            res.ticket_id.inventory_stage = 'draft'
        return res
