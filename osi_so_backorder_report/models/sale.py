# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

PRODUCT_TYPE_SELECTION = [
    ('consu', "Consumable"),
    ('service', "Service"),
    ('product', "Product")
]


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    adjusted_qty = fields.Float(string="Adjusted Quantity",compute="_compute_adjusted_quantity", store=True)
    last_date_delivered = fields.Datetime(string="Last Date Delivered", compute="_compute_last_date_delivered", store=True)
    last_bill_date = fields.Datetime(string="Last Bill Date", compute="_compute_last_bill_date", store=True)
    uigd_qty = fields.Float(string="UIGD Qty", compute='_compute_uigd_qty', store=True)
    bo_qty = fields.Float(string="Backorder Qty", compute='_compute_bo_qty', store=True)
    uigd_value = fields.Monetary(string="UIGD Value", compute='_compute_uigd_value', store=True)
    bo_value = fields.Monetary(string="Backorder Value", compute='_compute_bo_value', store=True)
    prod_type = fields.Selection(string="Product Type", selection=PRODUCT_TYPE_SELECTION, related="product_id.type")
    product_type = fields.Selection( string='Product Type', related='product_id.product_tmpl_id.type')
    product_std_price = fields.Monetary('UIGD Cost', compute='_compute_product_std_price', store=True)
    exclude_from_bo_report = fields.Boolean('Exclude From BO Report?')

    @api.depends('move_ids','move_ids.state')
    def _compute_adjusted_quantity(self):
        for line in self:
            line.adjusted_qty = sum(line.move_ids.filtered(
                lambda r: r.state != 'cancel' and r.location_dest_id.usage == 'customer').mapped('product_uom_qty'))
    
    @api.multi
    @api.depends('product_id', 'product_id.standard_price')
    def _compute_product_std_price(self):
        for line in self:
            line.product_std_price = line.product_id and line.product_id.standard_price or 0.0

    @api.multi
    @api.depends('qty_delivered','adjusted_qty')
    def _compute_bo_qty(self):
        for line in self:
            if line.product_id.type == 'product':
                line.bo_qty = line.adjusted_qty - line.qty_delivered
            else:
                line.bo_qty = 0

    @api.multi
    @api.depends('qty_delivered','qty_invoiced')
    def _compute_uigd_qty(self):
        for line in self:
            if line.product_id.type == 'product':
                line.uigd_qty = line.qty_delivered - line.qty_invoiced
            else:
                line.uigd_qty = 0

    @api.multi
    @api.depends('uigd_qty','price_unit')
    def _compute_uigd_value(self):
        for line in self:
            if line.product_uom_qty == 0:
                line.uigd_value = 0.0
                continue
            line.uigd_value = line.uigd_qty * (line.price_subtotal/line.product_uom_qty)

    @api.multi
    @api.depends('bo_qty','price_unit')
    def _compute_bo_value(self):
        for line in self:
            if line.product_uom_qty == 0:
                line.bo_value = 0.0
                continue
            line.bo_value = line.bo_qty * (line.price_subtotal/line.product_uom_qty)

    @api.multi
    @api.depends('qty_delivered','qty_invoiced')
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
    @api.depends('qty_delivered','qty_invoiced')
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
            line.last_bill_date = max_date and max_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) or False



class SaleOrder(models.Model):
    _inherit = "sale.order"

    last_date_delivered = fields.Datetime(string="Last Date Delivered", compute="_compute_last_date_delivered", store=True)
    last_bill_date = fields.Datetime(string="Last Bill Date", compute="_compute_last_bill_date", store=True)
    uigd_value = fields.Monetary(string="UIGD Value", compute='_compute_uigd_value', store=True)
    bo_value = fields.Monetary(string="Backorder Value", compute='_compute_bo_value', store=True)

    @api.multi
    @api.depends('order_line.uigd_value','order_line.price_unit')
    def _compute_uigd_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.uigd_value
            order.uigd_value = total
                

    @api.multi
    @api.depends('order_line.bo_value','order_line.price_unit')
    def _compute_bo_value(self):
        for order in self:
            total = 0
            for line in order.order_line:
                total += line.bo_value
            order.bo_value = total
    
    @api.multi
    @api.depends('order_line.last_date_delivered','order_line.qty_delivered','order_line.qty_invoiced')
    def _compute_last_date_delivered(self):
        for order in self:
            max_date = False
            for line in order.order_line:
                if max_date:
                    if line.last_date_delivered and max_date < line.last_date_delivered:
                        max_date = line.last_date_delivered
                else:
                    max_date = line.last_date_delivered
            order.last_date_delivered = max_date

    @api.depends('order_line.last_bill_date','order_line.qty_delivered','order_line.qty_invoiced')
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

