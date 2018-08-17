# -*- coding: utf-8 -*-
# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.depends('product_id', 'product_id.qty_available',
                 'product_id.outgoing_qty')
    def _product_qty_to_sell(self):
        """
            Returns the available products to Sell.
        """
        for rec in self:
            context = dict(rec._context)
            # Updating context
            context.update({'warehouse': rec.order_id.warehouse_id.id,
                            'location': rec.order_id.warehouse_id.lot_stock_id\
                            and rec.order_id.warehouse_id.lot_stock_id.id \
                            or False})
            # Get Availability of product
            res = rec.product_id.with_context(**context)._product_available()
            # Quantity on hand
            qty_available = res[rec.product_id.id]['qty_available']\
             if rec.product_id.id in res else 0
            # Get Reserved Qty
            reserved_qty = res[rec.product_id.id]['outgoing_qty']\
             if rec.product_id.id in res else 0
            # Update Available to Sell
            rec.qty_to_sell = qty_available - reserved_qty

    qty_to_sell = fields.Float(
                    string='Available to Sell',
                    digits=dp.get_precision('Product Unit of Measure'),
                    compute='_product_qty_to_sell'
                )
