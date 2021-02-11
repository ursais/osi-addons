# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    adjusted_qty = fields.Float(string="Adjusted Quantity",
        compute="_compute_adjusted_quantity", store=True)
    last_date_received = fields.Datetime(
        string="Last Date Received",
        compute="_compute_last_date_received", store=True)
    last_bill_date = fields.Datetime(
        string="Last Bill Date",
        compute="_compute_last_bill_date", store=True)
    uigr_qty = fields.Float(string="UIGR Qty",
                            compute='_compute_uigr_qty', store=True)
    bo_qty = fields.Float(string="Backorder Qty",
                          compute='_compute_bo_qty', store=True)
    uigr_value = fields.Monetary(string="UIGR Value",
                                 compute='_compute_uigr_value', store=True)
    bo_value = fields.Monetary(string="Backorder Value",
                               compute='_compute_bo_value', store=True)
    exclude_from_bo_report = fields.Boolean('Exclude From BO Report?')

    @api.depends('move_ids','move_ids.state')
    def _compute_adjusted_quantity(self):
        for line in self:
            line.adjusted_qty = sum(line.move_ids.filtered(
                lambda r: r.state != 'cancel' and r.location_id.usage == 'supplier').mapped('product_uom_qty'))

    @api.multi
    @api.depends('qty_received','adjusted_qty')
    def _compute_bo_qty(self):
        for line in self:
            if line.product_id.type in ('product','consu'):
                line.bo_qty = line.adjusted_qty - line.qty_received
            else:
                line.bo_qty = 0

    @api.multi
    @api.depends('qty_received','qty_invoiced')
    def _compute_uigr_qty(self):
        for line in self:
            if line.product_id.type in ('product','consu'):
                line.uigr_qty = line.qty_received - line.qty_invoiced
            else:
                line.uigr_qty = 0

    @api.multi
    @api.depends('uigr_qty','price_unit')
    def _compute_uigr_value(self):
        for line in self:
            if line.product_uom_qty == 0:
                line.uigr_value = 0.0
                continue
            line.uigr_value = line.uigr_qty * (line.price_subtotal/line.product_uom_qty)

    @api.multi
    @api.depends('bo_qty','price_unit')
    def _compute_bo_value(self):
        for line in self:
            if line.product_uom_qty == 0:
                line.bo_value = 0.0
                continue
            line.bo_value = line.bo_qty * (line.price_subtotal/line.product_uom_qty)

    @api.multi
    @api.depends('order_id.state', 'move_ids.state',
                 'move_ids.product_uom_qty')
    def _compute_last_date_received(self):
        for line in self:
            max_date = False
            for move in line.move_ids:
                if move.state == 'done':
                    if move.location_dest_id.usage == "supplier":
                        if move.to_refund:
                            continue
                    else:
                        if max_date:
                            if max_date < move.date:
                                max_date = move.date
                        else:
                            max_date = move.date
            line.last_date_received = max_date

    @api.depends('invoice_lines.invoice_id.state',
                 'invoice_lines.quantity')
    def _compute_last_bill_date(self):
        for line in self:
            max_date = False
            for inv_line in line.invoice_lines:
                if inv_line.invoice_id.state not in ['cancel']:
                    if inv_line.invoice_id.type == 'in_invoice':
                        if max_date and inv_line.invoice_id.date:
                            if max_date < inv_line.invoice_id.date:
                                    max_date = inv_line.invoice_id.date
                        else:
                            max_date = inv_line.invoice_id.date
                    elif inv_line.invoice_id.type == 'in_refund':
                        continue
            line.last_bill_date = max_date and max_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) or False

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    last_date_received = fields.Datetime(
        string="Last Date Received",
        compute="_compute_last_date_received", store=True)
    last_bill_date = fields.Datetime(
        string="Last Bill Date",
        compute="_compute_last_bill_date", store=True)
    uigr_value = fields.Monetary(string="UIGR Value",
                                 compute='_compute_uigr_value', store=True)
    bo_value = fields.Monetary(string="Backorder Value",
                               compute='_compute_bo_value', store=True)
    product_type = fields.Selection(related='product_id.product_tmpl_id.type',
                                    string='Product Type')


    @api.multi
    @api.depends('order_line.uigr_value','order_line.price_unit')
    def _compute_uigr_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.uigr_value
            order.uigr_value = total
                
    @api.multi
    @api.depends('order_line.bo_value','order_line.price_unit')
    def _compute_bo_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.bo_value
            order.bo_value = total



    @api.multi
    @api.depends('order_line.last_date_received','order_line.qty_received','order_line.qty_invoiced')
    def _compute_last_date_received(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if max_date:
                    if line.last_date_received and max_date < line.last_date_received:
                        max_date = line.last_date_received
                else:
                    max_date = line.last_date_received
            order.last_date_received = max_date

    @api.depends('order_line.last_bill_date','order_line.qty_received','order_line.qty_invoiced')
    def _compute_last_bill_date(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if max_date:
                    if line.last_bill_date and max_date < line.last_bill_date:
                        max_date = line.last_bill_date
                else:
                    max_date = line.last_bill_date
            order.last_bill_date = max_date


