# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.
import logging
import re
from odoo import api, fields, models
from odoo.osv import expression
_logger = logging.getLogger(__name__)


class ShProductTemplate(models.Model):
    _inherit = 'product.template'

    sh_product_customer_ids = fields.One2many(
        'sh.product.customer.info', 'product_tmpl_id', string="Customer Code")

    code_id = fields.Char(
        related='sh_product_customer_ids.product_code', string='Code', readonly=False)

    product_code_name = fields.Char(
        related='sh_product_customer_ids.product_name', string='Customer Product Name', readonly=False)

    @api.model
    def create(self, vals):
        res = super(ShProductTemplate, self).create(vals)

        if res:
            product_variant = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', res.id)])

            if (
                customer_code := self.env['sh.product.customer.info']
                .sudo()
                .search([('product_tmpl_id', '=', res.id)], order='id desc')
            ):
                for code in customer_code:
                    code.write(
                        {'product_id': product_variant or product_variant[0] or False})
        return res


class ShProductProduct(models.Model):
    _inherit = 'product.product'
    
    sh_product_customer_ids = fields.One2many(
        'sh.product.customer.info', 'product_id', string="Customer Code")
    
    code_id = fields.Char(
        related='sh_product_customer_ids.product_code', string='Code', readonly=False)

    product_code_name = fields.Char(
        related='sh_product_customer_ids.product_name', string='Customer Product Name', readonly=False)

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            sh_partner_id = self._context.get('partner_id')
            partners = [sh_partner_id]
            if sh_partner_id:
                if partner := self.env['res.partner'].browse(sh_partner_id):
                    if partner.child_ids:
                        partners.extend(
                            child.id for child in partner.child_ids)
                    if partner.parent_id:
                        partners.append(partner.parent_id.id)
                        if partner.parent_id.child_ids:
                            partners.extend(
                                child.id for child in partner.parent_id.child_ids)
                if customer_ids := self.env['sh.product.customer.info']._search([('name', 'in', partners), '|', ('product_code', operator, name), ('product_name', operator, name)], order=order):
                    return self._search(
                        [('product_tmpl_id.sh_product_customer_ids', 'in', customer_ids)], limit=limit, order=order)
            # SH

            if operator in positive_operators:
                product_ids = list(self._search(
                    [('default_code', '=', name)] + domain, limit=limit, order=order)) or list(self._search(
                        [('barcode', '=', name)] + domain, limit=limit, order=order))
            if not product_ids:
                if operator not in expression.NEGATIVE_TERM_OPERATORS:
                    # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                    # on a database with thousands of matching products, due to the huge merge+unique needed for the
                    # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                    # Performing a quick memory merge of ids in Python will give much better performance
                    product_ids = list(self._search(
                        domain + [('default_code', operator, name)], limit=limit, order=order))
                    if not limit or len(product_ids) < limit:
                        # we may underrun the limit because of dupes in the results, that's fine
                        limit2 = (limit - len(product_ids)) if limit else False
                        product2_ids = self._search(
                            domain + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, order=order)
                        product_ids.extend(product2_ids)
                else:
                    domain2 = expression.OR([
                        ['&', ('default_code', operator, name),
                         ('name', operator, name)],
                        ['&', ('default_code', '=', False),
                         ('name', operator, name)],
                    ])
                    domain2 = expression.AND([domain, domain2])
                    product_ids = list(self._search(
                        domain2, limit=limit, order=order))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                if res := ptrn.search(name):
                    product_ids = list(self._search(
                        [('default_code', '=', res.group(2))] + domain, limit=limit, order=order))
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                if suppliers_ids := self.env['product.supplierinfo']._search(
                    [
                        ('partner_id', '=', self._context.get('partner_id')),
                        '|',
                        ('product_code', operator, name),
                        ('product_name', operator, name),
                    ]
                ):
                    product_ids = self._search(
                        [('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, order=order)
        else:
            product_ids = self._search(domain, limit=limit, order=order)
        return product_ids
