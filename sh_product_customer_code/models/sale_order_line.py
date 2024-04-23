# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    sh_line_customer_code = fields.Char('Customer Product Code')
    sh_line_customer_product_name = fields.Char('Customer Product Name')

    @api.model_create_multi
    def create(self, vals_list):
        res_super = super(SaleOrderLine, self).create(vals_list)
        for res in res_super:
            print("\n\n\n\n\n\n self.env.company.enable_pro_code_from_so",self.env.company.enable_pro_code_from_so)
            if res and self.env.company.enable_pro_code_from_so:
                print("\n\n\n\n\n\n INNNNNNNNNNNNNNNN self.env.company.enable_pro_code_from_so",self.env. company.enable_pro_code_from_so)
                code = self.env['sh.product.customer.info'].search([('name', '=', res.order_id.partner_id.id), ('product_code', '=', res.sh_line_customer_code),
                                                                    ('product_name', '=', res.sh_line_customer_product_name)], limit=1)

                if not self.product_id and not code and (res.sh_line_customer_code or res.sh_line_customer_product_name):
                    self.product_id.sh_product_customer_ids.sudo().create({
                        'name': res.order_id.partner_id.id,
                        'product_tmpl_id': res.product_id.product_tmpl_id.id,
                        'product_id': res.product_id.id,
                        'product_code': res.sh_line_customer_code,
                        'product_name': res.sh_line_customer_product_name,
                    })

        return res_super

    def write(self, values):
        result = super(SaleOrderLine, self).write(values)

        if self.env.company.enable_pro_code_from_so and (values and values.get('sh_line_customer_code') or values.get('sh_line_customer_product_name')):
            code = self.env['sh.product.customer.info'].search([('name', '=', self.order_id.partner_id.id), ('product_code', '=', values.get(
                'sh_line_customer_code')), ('product_name', '=', values.get('sh_line_customer_product_name'))], limit=1)

            if not code:
                self.env['sh.product.customer.info'].sudo().create({
                    'name': self.order_id.partner_id.id,
                    'product_tmpl_id': self.product_id.product_tmpl_id.id,
                    'product_id': self.product_id.id,
                    'product_code': values.get('sh_line_customer_code') or self.sh_line_customer_code,
                    'product_name': values.get('sh_line_customer_product_name') or self.sh_line_customer_product_name,
                })
        return result

    @api.onchange('product_id')
    def _onchange_product_id_warning(self):
        res = super(SaleOrderLine, self)._onchange_product_id_warning()
        partners = []
        for line in self:
            if line.product_id:
                # Partner Parent Child Record Can Show now
                partners.append(line.order_id.partner_id.id)
                if line.order_id and line.order_id.partner_id:
                    if line.order_id.partner_id.child_ids:
                        partners.extend(
                            child.id for child in line.order_id.partner_id.child_ids)
                    if line.order_id.partner_id.parent_id:
                        partners.append(line.order_id.partner_id.parent_id.id)
                        if line.order_id.partner_id.parent_id.child_ids:
                            partners.extend(
                                child.id
                                for child in line.order_id.partner_id.parent_id.child_ids
                            )
                customer_code = self.env['sh.product.customer.info'].sudo().search(
                    [('name', 'in', partners), '|', ('product_id', '=', line.product_id.id), ('product_tmpl_id', '=', line.product_id.id)],  order='id desc', limit=1)

                line.sh_line_customer_code = customer_code.product_code if customer_code and customer_code.product_code else False
                line.sh_line_customer_product_name = customer_code.product_name if customer_code and customer_code.product_name else False

                if self.product_id and customer_code:
                    des = " "

                    if customer_code.product_code:
                        des += f"[{customer_code.product_code}]"
                    if customer_code.product_name:
                        des += customer_code.product_name
                    line.name = des
        return res
