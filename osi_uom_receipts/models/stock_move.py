# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'


    def create(self, vals_list):
        res = super().create(vals_list)

        for record in res:
            if record.purchase_line_id and record.purchase_line_id.product_uom  != record.product_uom:
                
                record.update({
                    'product_uom':record.purchase_line_id.product_uom.id,
                    'product_uom_qty':record.purchase_line_id.product_qty
                })
        return res
