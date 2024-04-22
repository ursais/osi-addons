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

class srPurchasePriceHistory(models.Model):
    _name = 'sr.purchase.price.history'
    _description = 'Purchase Price History'

    name = fields.Many2one("purchase.order.line",string="Purchase Order Line")  
    partner_id = fields.Many2one("res.partner",string="Customer")
    user_id = fields.Many2one("res.users",string="Sales Person")
    product_tmpl_id = fields.Many2one("product.template",string="Template Id")
    variant_id = fields.Many2one("product.product",string="Product")
    purchase_order_id = fields.Many2one("purchase.order",string="Purchase Order")
    purchase_order_date = fields.Datetime(string="Purchase Order Date")
    product_uom_qty = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Price")
    currency_id = fields.Many2one("res.currency",string="Currency Id")
    total_price = fields.Monetary(string="Total")

