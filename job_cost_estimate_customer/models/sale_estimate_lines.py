# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class SaleEstimatelineJob(models.Model):
    _name = "sale.estimate.line.job"
    _description = 'Sale Estimate line Job'
    
    @api.depends('price_unit','product_uom_qty','discount')
    def _compute_amount(self):
        for rec in self:
            if rec.discount:
                disc_amount = (rec.price_unit * rec.product_uom_qty) * rec.discount / 100
                rec.price_subtotal = (rec.price_unit * rec.product_uom_qty) - disc_amount
            else:
                rec.price_subtotal = rec.price_unit * rec.product_uom_qty
            
    estimate_id = fields.Many2one(
        'sale.estimate.job',
        string='Sale Estimate', 
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    product_uom_qty = fields.Float(
        string='Quantity', 
        #digits=dp.get_precision('Product Unit of Measure'), 
        required=True, 
        default=1.0,
        digits='Product Unit of Measure',
    )
    product_uom = fields.Many2one(
        'uom.uom', #produtc.uom
        string='Unit of Measure', 
        required=True
    )
    price_unit = fields.Float(
        'Unit Price', 
        required=True, 
        #digits=dp.get_precision('Product Price'), 
        default=0.0,
        digits='Product Price',
    )
    price_subtotal = fields.Float(
        compute='_compute_amount', 
        string='Subtotal', 
        store=True,
        digits='Product Price',
    )
    product_description = fields.Char(
        string='Description'
    )
    discount = fields.Float(
        string='Discount (%)',
    )
    company_id = fields.Many2one(related='estimate_id.company_id', string='Company', store=True, readonly=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    job_type = fields.Selection(
        selection=[('material','Material'),
                   ('labour','Labour'),
                    ('overhead','Overhead')
                ],
        string="Type",
        required=True,
    )
    analytic_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        # store=True,
    )

    # @api.multi
    # @api.onchange('product_id')
    # def product_id_change(self):
    #     if not self.product_id:
    #         return {'domain': {'product_uom': []}}

    #     vals = {}
    #     domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
    #     if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
    #         vals['product_uom'] = self.product_id.uom_id
    #         vals['product_uom_qty'] = 1.0

    #     product = self.product_id.with_context(
    #         lang=self.estimate_id.partner_id.lang,
    #         partner=self.estimate_id.partner_id.id,
    #         quantity=vals.get('product_uom_qty') or self.product_uom_qty,
    #         date=self.estimate_id.estimate_date,
    #         pricelist=self.estimate_id.pricelist_id.id,
    #         uom=self.product_uom.id
    #     )

    #     name = product.name_get()[0][1]
    #     if product.description_sale:
    #         name += '\n' + product.description_sale
    #     vals['product_description'] = name

    #     self._compute_tax_id()

    #     if self.estimate_id.pricelist_id and self.estimate_id.partner_id:
    #         vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
    #     self.update(vals)

    #     title = False
    #     message = False
    #     warning = {}
    #     if product.sale_line_warn != 'no-message':
    #         title = _("Warning for %s") % product.name
    #         message = product.sale_line_warn_msg
    #         warning['title'] = title
    #         warning['message'] = message
    #         if product.sale_line_warn == 'block':
    #             self.product_id = False
    #         return {'warning': warning}
    #     return {'domain': domain}

    # @api.multi
    # def _compute_tax_id(self):
    #     for line in self:
    #         fpos = line.estimate_id.partner_id.property_account_position_id
    #         # If company_id is set, always filter taxes by the company
    #         taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
    #         # line.tax_id = fpos.map_tax(taxes, line.product_id, line.estimate_id.partner_id) if fpos else taxes
    #         line.tax_id = fpos.map_tax(taxes)#14 feb 2022

    def _compute_tax_id(self): #14 feb 2022
        for line in self:
            line = line.with_company(line.company_id)
            # fpos = self.env['account.fiscal.position'].get_fiscal_position(line.estimate_id.partner_id.id)
            fpos = self.env['account.fiscal.position']._get_fiscal_position(line.estimate_id.partner_id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes)

    def _get_custom_pricelist_item_id(self):
        for line in self:
            if not line.product_id or not line.estimate_id.pricelist_id:
                pricelist_item_id = False
            else:
                pricelist_item_id = line.estimate_id.pricelist_id._get_product_rule(
                    line.product_id,
                    line.product_uom_qty or 1.0,
                    uom=line.product_uom,
                    date=line.estimate_id.estimate_date,
                )

            pricelist_item = pricelist_item_id

            pricelist_rule = self.env['product.pricelist.item'].browse(pricelist_item)

            order_date = line.estimate_id.estimate_date or fields.Date.today()
            product = line.product_id
            qty = line.product_uom_qty or 1.0
            uom = line.product_uom or line.product_id.uom_id

            price = pricelist_rule._compute_price(
                # product, qty, uom, order_date, currency=self.currency_id)
                product, qty, uom, order_date, currency=line.estimate_id.pricelist_id.currency_id)
        return price

    def _get_pricelist_price_before_discount(self):
        for line in self:
            pricelist_item_id = line.estimate_id.pricelist_id._get_product_rule(
                        line.product_id,
                        line.product_uom_qty or 1.0,
                        uom=line.product_uom,
                        date=line.estimate_id.estimate_date,
                    )
            pricelist_rule = self.env['product.pricelist.item'].browse(pricelist_item_id)

            order_date = line.estimate_id.estimate_date or fields.Date.today()
            product = line.product_id
            qty = line.product_uom_qty or 1.0
            uom = line.product_uom

            if pricelist_rule:
                pricelist_item = pricelist_rule
                if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                    # Find the lowest pricelist rule whose pricelist is configured
                    # to show the discount to the customer.
                    while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                        rule_id = pricelist_item.base_pricelist_id._get_product_rule(
                            product, qty, uom=uom, date=order_date)
                        pricelist_item = self.env['product.pricelist.item'].browse(rule_id)

                pricelist_rule = pricelist_item

            price = pricelist_rule._compute_base_price(
                product,
                qty,
                uom,
                order_date,
                target_currency=self.estimate_id.pricelist_id.currency_id,
            )

        return price
       

    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order

        pricelist_price = self._get_custom_pricelist_item_id()

        if self.estimate_id.pricelist_id.discount_policy == 'with_discount':
            # return product.with_context(pricelist=self.estimate_id.pricelist_id.id,  uom=self.product_uom.id).price
            return pricelist_price
        # product_context = dict(self.env.context, partner_id=self.estimate_id.partner_id.id, date=self.estimate_id.estimate_date, uom=self.product_uom.id)#

        # final_price, rule_id = self.estimate_id.pricelist_id.with_context(product_context).get_product_price_rule(product or self.product_id, self.product_uom_qty or 1.0, self.estimate_id.partner_id)
        # base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, 
        #     self.product_uom, self.estimate_id.pricelist_id.id)
        # if currency != self.estimate_id.pricelist_id.currency_id: #
        #     base_price = currency._convert(
        #         base_price, self.estimate_id.pricelist_id.currency_id,
        #         self.estimate_id.company_id or self.env.company, self.estimate_id.estimate_date or fields.Date.today()) #

        base_price = self._get_pricelist_price_before_discount()

        # return max(base_price, final_price)
        return max(base_price, pricelist_price)


    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            partner=self.estimate_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.estimate_id.estimate_date,
            pricelist=self.estimate_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['product_description'] = name

        self._compute_tax_id()

        if self.estimate_id.pricelist_id and self.estimate_id.partner_id:
            vals['price_unit'] = product._get_tax_included_unit_price(
                self.company_id,
                self.estimate_id.currency_id,
                self.estimate_id.estimate_date,
                'sale',
                product_price_unit=self._get_display_price(product),
                product_currency=self.estimate_id.currency_id
            )

        # if self.estimate_id.pricelist_id and self.estimate_id.partner_id:
        #     vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
        self.update(vals)

        title = False
        message = False
        warning = {}

        product = self.product_id
        if product and product.sale_line_warn != 'no-message':
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {
                'warning': {
                    'title': _("Warning for %s", product.name),
                    'message': product.sale_line_warn_msg,
                }
            }

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            # if pricelist_item.pricelist_id.discount_policy == 'without_discount':
            #     while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
            #         _price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty, self.estimate_id.partner_id)
            #         pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                # Find the lowest pricelist rule whose pricelist is configured
                # to show the discount to the customer.
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    rule_id = pricelist_item.base_pricelist_id._get_product_rule(
                        product, qty, uom=uom, date=order_date)
                    pricelist_item = self.env['product.pricelist.item'].browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.company_id or self.env.company, self.estimate_id.estimate_date or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty', 'tax_id')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom and
                self.estimate_id.partner_id and self.estimate_id.pricelist_id and
                self.estimate_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.estimate_id.partner_id.lang,
            partner=self.estimate_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.estimate_id.estimate_date,
            pricelist=self.estimate_id.pricelist_id.id,
            uom=self.product_uom.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.estimate_id.partner_id.id, date=self.estimate_id.estimate_date, uom=self.product_uom.id)

        # price, rule_id = self.estimate_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.estimate_id.partner_id)
        price, rule_id = self.estimate_id.pricelist_id.with_context(product_context)._get_product_price_rule(self.product_id, self.product_uom_qty or 1.0)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom, self.estimate_id.pricelist_id.id)

        if new_list_price != 0:
            if self.estimate_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.estimate_id.pricelist_id.currency_id,
                    self.estimate_id.company_id or self.env.company, self.estimate_id.estimate_date or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                self.discount = discount

        # if product.sale_line_warn != 'no-message':
        #     title = _("Warning for %s") % product.name
        #     message = product.sale_line_warn_msg
        #     warning['title'] = title
        #     warning['message'] = message
        #     if product.sale_line_warn == 'block':
        #         self.product_id = False
        #     return {'warning': warning}
        # return {'domain': domain}

    # @api.multi
    # def _get_display_price(self, product):
    #     if self.estimate_id.pricelist_id.discount_policy == 'without_discount':
    #         from_currency = self.estimate_id.company_id.currency_id
    #         return from_currency.compute(product.lst_price, self.estimate_id.pricelist_id.currency_id)
    #     return product.with_context(pricelist=self.estimate_id.pricelist_id.id).price
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
