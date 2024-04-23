# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sh_line_customer_code = fields.Char(string='Customer Product Code')
    sh_line_customer_product_name = fields.Char(string='Customer Product Name')

    @api.model_create_multi
    def create(self, vals_list):
        res_super = super(AccountMoveLine, self).create(vals_list)
        for rec in res_super:
            if rec.product_id:
                # Partner Parent Child Record Can Show now
                partners = [rec.move_id.partner_id.id]
                if rec.move_id.partner_id:
                    if rec.move_id.partner_id.child_ids:
                        partners.extend(
                            child.id for child in rec.move_id.partner_id.child_ids)
                    if rec.move_id.partner_id.parent_id:
                        partners.append(rec.move_id.partner_id.parent_id.id)
                        if rec.move_id.partner_id.parent_id.child_ids:
                            partners.extend(
                                child.id
                                for child in rec.move_id.partner_id.parent_id.child_ids
                            )
                customer_code = self.env['sh.product.customer.info'].sudo(
                ).search([('name', 'in', partners),
                          ('product_id', '=', rec.product_id.id)],
                         limit=1)
                rec.sh_line_customer_code = customer_code.product_code if customer_code and customer_code.product_code else False
                rec.sh_line_customer_product_name = customer_code.product_name if customer_code and customer_code.product_name else False

        return res_super

    @api.onchange('product_id')
    def _inverse_product_id(self):
        res = super(AccountMoveLine, self)._inverse_product_id()

        for line in self:
            if line.product_id:
                # Partner Parent Child Record Can Show now
                partners = [line.move_id.partner_id.id]
                if line.move_id.partner_id:
                    if line.move_id.partner_id.child_ids:
                        partners.extend(
                            child.id for child in line.move_id.partner_id.child_ids)
                    if line.move_id.partner_id.parent_id:
                        partners.append(line.move_id.partner_id.parent_id.id)
                        if line.move_id.partner_id.parent_id.child_ids:
                            partners.extend(
                                child.id
                                for child in line.move_id.partner_id.parent_id.child_ids
                            )
                customer_code = self.env['sh.product.customer.info'].sudo(
                ).search([('name', 'in', partners),
                          ('product_id', '=', line.product_id.id)],
                         limit=1)
                line.sh_line_customer_code = customer_code.product_code if customer_code and customer_code.product_code else False
                line.sh_line_customer_product_name = customer_code.product_name if customer_code and customer_code.product_name else False

        return res
