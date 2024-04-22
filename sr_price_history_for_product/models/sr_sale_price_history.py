# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Skype : contact.hiren1188
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class srSalePriceHistory(models.Model):
    _name = 'sr.sale.price.history'
    _description = 'Sale Price History'

    name = fields.Many2one("sale.order.line",string="Sale Order Line")  
    partner_id = fields.Many2one("res.partner",string="Customer")
    user_id = fields.Many2one("res.users",string="Sales Person")
    product_tmpl_id = fields.Many2one("product.template",string="Template Id")
    variant_id = fields.Many2one("product.product",string="Product")
    sale_order_id = fields.Many2one("sale.order",string="Sale Order")
    sale_order_date = fields.Datetime(string="Order Date")
    product_uom_qty = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Price")
    currency_id = fields.Many2one("res.currency",string="Currency Id")
    total_price = fields.Monetary(string="Total")


