# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, fields, models


class ShProductCustomerCode(models.Model):
    _name = 'sh.product.customer.info'
    _description = "Sh Product Customer Code"

    @api.model
    def default_get(self, fields_list):
        res = super(ShProductCustomerCode, self).default_get(fields_list)
        active_id = self.env.context.get('default_product_tmpl_id')
        product = self.env['product.template'].sudo().browse(active_id)

        if product.product_variant_count <= 1:
            product_variant = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', product.id)])
            res.update({'product_id': product_variant.id})

        return res

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        if self.product_tmpl_id.product_variant_count <= 1:
            product_variant = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', self.product_tmpl_id.id)])
            self.update({'product_id': product_variant.id})
        else:
            self.update({'product_id': False})

    name = fields.Many2one(
        'res.partner', 'Customer',
        ondelete='cascade', required=True,
        help="Customer of this product")

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template',
        index=True, ondelete='cascade')

    product_id = fields.Many2one(
        'product.product', 'Product Variant', index=True,
        help="If not set, the vendor price will apply to all variants of this product.")

    product_name = fields.Char(
        'Customer Product Name',
        help="This vendor's product name will be used when printing a request for quotation. Keep empty to use the internal one.")
    product_code = fields.Char(
        'Customer Product Code',
        help="This vendor's product code will be used when printing a request for quotation. Keep empty to use the internal one.")
