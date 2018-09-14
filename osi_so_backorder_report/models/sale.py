# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    last_date_delivered = fields.Datetime(
        string="Last Date Delivered",
        compute="_compute_last_date_delivered",
        store=True
    )
    last_bill_date = fields.Datetime(
        string="Last Bill Date",
        compute="_compute_last_bill_date",
        store=True
    )
    uigd_value = fields.Monetary(
        string="UIGD Value",
        compute="_compute_uigd_value",
        store=True
    )
    bo_value = fields.Monetary(
        string="Backorder Value",
        compute="_compute_bo_value",
        store=True
    )

    @api.multi
    @api.depends('order_line.uigd_qty', 'order_line.price_unit')
    def _compute_uigd_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.uigd_value
            order.uigd_value = total

    @api.multi
    @api.depends('order_line.bo_qty', 'order_line.price_unit')
    def _compute_bo_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.bo_value
            order.bo_value = total

    @api.multi
    @api.depends('order_line.last_date_delivered', 'order_line.qty_delivered',
                 'order_line.qty_invoiced')
    def _compute_last_date_delivered(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if max_date:
                    if (line.last_bill_date and
                            max_date < line.last_date_delivered):
                        max_date = line.last_date_delivered
                else:
                    max_date = line.last_date_delivered
            order.last_date_delivered = max_date

    @api.multi
    @api.depends('order_line.last_bill_date', 'order_line.qty_delivered',
                 'order_line.qty_invoiced')
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


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    last_date_delivered = fields.Datetime(
        string="Last Date Delivered",
        compute="_compute_last_date_delivered",
        store=True
    )
    last_bill_date = fields.Datetime(
        string="Last Bill Date",
        compute="_compute_last_bill_date",
        store=True
    )
    uigd_qty = fields.Float(
        string="UIGD Qty",
        compute='_compute_uigd_qty',
        store=True
    )
    bo_qty = fields.Float(
        string="Backorder Qty",
        compute='_compute_bo_qty',
        store=True
    )
    uigd_value = fields.Monetary(
        string="UIGD Value",
        compute='_compute_uigd_value',
        store=True
    )
    bo_value = fields.Monetary(
        string="Backorder Value",
        compute='_compute_bo_value',
        store=True
    )

    @api.multi
    @api.depends('qty_delivered', 'product_uom_qty')
    def _compute_bo_qty(self):
        for line in self:
            line.bo_qty = line.product_uom_qty - line.qty_delivered

    @api.multi
    @api.depends('qty_delivered', 'qty_invoiced')
    def _compute_uigd_qty(self):
        for line in self:
            line.uigd_qty = line.qty_delivered - line.qty_invoiced

    @api.multi
    @api.depends('uigd_qty', 'price_unit')
    def _compute_uigd_value(self):
        for line in self:
            line.uigd_value = line.uigd_qty * line.price_unit

    @api.multi
    @api.depends('bo_qty', 'price_unit')
    def _compute_bo_value(self):
        for line in self:
            line.bo_value = line.bo_qty * line.price_unit

    @api.multi
    @api.depends('qty_delivered', 'qty_invoiced')
    def _compute_last_date_delivered(self):
        for line in self:
            max_date = False
            for move in line.move_ids:
                if move.state == 'done':
                    if move.location_dest_id.usage == "customer":
                        if move.to_refund:
                            continue
                        else:
                            if max_date:
                                if max_date < move.date:
                                    max_date = move.date
                            else:
                                max_date = move.date
            line.last_date_delivered = max_date

    @api.multi
    @api.depends('qty_delivered', 'qty_invoiced')
    def _compute_last_bill_date(self):
        for line in self:
            max_date = False
            for inv_line in line.invoice_lines:
                if inv_line.invoice_id.state not in ['cancel']:
                    if inv_line.invoice_id.type == 'out_invoice':
                        if max_date and inv_line.invoice_id.date:
                            if max_date < inv_line.invoice_id.date:
                                    max_date = inv_line.invoice_id.date
                        else:
                            max_date = inv_line.invoice_id.date
                    elif inv_line.invoice_id.type == 'out_refund':
                        continue
            line.last_bill_date = max_date
