# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line'
    )
    sc_flag = fields.Boolean(
        related='sale_line_id.sc_flag',
        string='Store Credit Product Flag',
        store=True
    )
    gift_flag = fields.Boolean(
        related='sale_line_id.gift_flag',
        string='Gift Card Product Flag',
        store=True
    )
    first_time_gc_flag = fields.Boolean(
        string='First Time GC flag',
        default=False
    )

    @api.multi
    def unlink(self):
        for line in self:
            if line.sc_flag:
                self.sale_line_id.write({
                    'remaining_sc_amount':
                        self.sale_line_id.remaining_sc_amount -
                        self.price_unit})
            elif line.gift_flag:
                if not line.first_time_gc_flag:
                    self.sale_line_id.write({
                        'remaining_gift_amount':
                            self.sale_line_id.remaining_gift_amount -
                            self.price_unit})
        return super(AccountInvoiceLine, self).unlink()


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('invoice_line_ids.price_subtotal')
    def _compute_lines(self):
        for invoice in self:
            inv_sc_lines = 0
            inv_gift_lines = 0
            sale_sc_lines = 0
            sale_gift_lines = 0

            if invoice.sale_id:
                for line in invoice.invoice_line_ids:
                    if line.product_id and line.sale_line_id.sc_flag:
                        inv_sc_lines += 1
                    elif line.product_id and line.sale_line_id.gift_flag:
                        inv_gift_lines += 1
                for order_line in invoice.sale_id.order_line:
                    if order_line.sc_flag:
                        sale_sc_lines += 1
                    elif order_line.gift_flag:
                        sale_gift_lines += 1

            invoice.inv_sc_lines = inv_sc_lines
            invoice.inv_gift_lines = inv_gift_lines
            invoice.sale_sc_lines = sale_sc_lines
            invoice.sale_gift_lines = sale_gift_lines

    sale_id = fields.Many2one(
        'sale.order',
        related='invoice_line_ids.sale_line_id.order_id',
        string='Sale Order',
        store=True
    )
    inv_sc_lines = fields.Integer(
        string='Inv SC Line',
        store=True,
        readonly=True,
        compute='_compute_lines'
    )
    inv_gift_lines = fields.Integer(
        string='Inv Gift Line',
        store=True,
        readonly=True,
        compute='_compute_lines'
    )
    sale_sc_lines = fields.Integer(
        string='Sale SC Line',
        store=True,
        readonly=True,
        compute='_compute_lines'
    )
    sale_gift_lines = fields.Integer(
        string='Sale Gift Line',
        store=True,
        readonly=True,
        compute='_compute_lines'
    )

    @api.multi
    def _create_store_credit_product(self, sale_line_sc_id, sale_sc_total):
        # get store credit product
        if self.company_id and self.company_id.store_credit_product_id:
            product_id = self.company_id.store_credit_product_id
            account_id = product_id.property_account_income
            if not account_id:
                account_id = product_id.categ_id.property_account_income_categ
            if not account_id:
                raise UserError(_('Please define income account for '
                                  'this product: "%s" (id:%d).')
                                % (product_id.name, product_id.id,))

            return self.env['account.invoice.line'].create({
                'product_id': product_id.id,
                'account_id': account_id.id,
                'price_unit': -(sale_sc_total),
                'quantity': 1,
                'name': product_id.name,
                'sale_line_id': sale_line_sc_id.id,
                'invoice_id': self.id
            })
        return True

    @api.multi
    def _create_gift_card_product(self, sale_line_gift_id, sale_gift_total):
        # get store credit product
        if self.company_id and self.company_id.gift_card_product_id:

            product_id = self.company_id.gift_card_product_id
            account_id = product_id.property_account_income
            if not account_id:
                account_id = product_id.categ_id.property_account_income_categ
            if not account_id:
                raise UserError(_('Please define income account for '
                                  'this product: "%s" (id:%d).')
                                % (product_id.name, product_id.id,))

            return self.env['account.invoice.line'].create({
                'product_id': product_id.id,
                'account_id': account_id.id,
                'price_unit': -(sale_gift_total),
                'quantity': 1,
                'name': product_id.name,
                'sale_line_id': sale_line_gift_id.id,
                'invoice_id': self.id
            })
        return True

    @api.multi
    def compute_taxes(self):
        # Make a super method call
        super(AccountInvoice, self).compute_taxes()
        # browse invoice
        for invoice in self:
            # set total for non Store credit and Gift card product
            product_total = sum(line.price_subtotal for line in
                                self.invoice_line_ids if line.sale_line_id
                                and not line.sale_line_id.sc_flag and
                                not line.sale_line_id.gift_flag)

            # check amount_total is negativ and type = out_invoice
            if invoice.amount_total < 0.0 \
                    and invoice.type == 'out_invoice' \
                    or invoice.sale_sc_lines >= 1 \
                    and invoice.inv_sc_lines >= 1:
                # search Store credit product in Invoice line
                sc_invoice_id = self.env['account.invoice.line'].search([
                    ('invoice_id', '=', invoice.id),
                    ('sc_flag', '=', True)])

                # search Credit Card product in Invoice line
                gift_invoice_id = self.env['account.invoice.line'].search([
                    ('invoice_id', '=', invoice.id),
                    ('gift_flag', '=', True)])

                # sc amount is grether then 0 in Sale order line
                if sc_invoice_id and\
                        sc_invoice_id.sale_line_id.remaining_sc_amount > 0.0:
                    # check remaining sc amount with invoice non sc/gc
                    # amount total
                    if sc_invoice_id.sale_line_id.remaining_sc_amount \
                            >= product_total:
                        # update invoice line with new calculation amount
                        sc_invoice_id.write({'price_unit': -(product_total)})
                        # update sale line remaining Store credit amount
                        sc_invoice_id.sale_line_id.write({
                            'remaining_sc_amount':
                                sc_invoice_id.sale_line_id.remaining_sc_amount
                                - product_total})
                        if gift_invoice_id:
                            gift_invoice_id.write({'first_time_gc_flag': True})
                            gift_invoice_id.unlink()
                    else:
                        remaining_product_total = \
                            product_total - \
                            sc_invoice_id.sale_line_id.remaining_sc_amount
                        # update invoice line with new calculation amount
                        sc_invoice_id.write({'price_unit': -(
                            sc_invoice_id.sale_line_id.remaining_sc_amount)})
                        # update sale line remaining Store credit amount
                        sc_invoice_id.sale_line_id.write({
                            'remaining_sc_amount': 0.0})
                        # search Credit Card product in Invoice line
                        gift_invoice_id = self.env['account.invoice.line'].\
                            search([('invoice_id', '=', invoice.id),
                                    ('gift_flag', '=', True)])
                        remaining_gift_amount = \
                            gift_invoice_id.sale_line_id.remaining_gift_amount
                        if gift_invoice_id and remaining_gift_amount > 0.0:
                            # check remaining sc amount with invoice non sc/gc
                            # amount total
                            if remaining_gift_amount \
                                    >= remaining_product_total:
                                # update invoice line with new calculate amount
                                gift_invoice_id.write({
                                    'price_unit': -(remaining_product_total)})
                                # update sale line remaining gc amount
                                gift_invoice_id.sale_line_id.write({
                                    'remaining_gift_amount':
                                        remaining_gift_amount -
                                        remaining_product_total})
                            else:
                                # update invoice line with new calculate amount
                                gift_invoice_id.write({
                                    'price_unit': -(remaining_gift_amount)})
                                # update sale line remaining gc amount
                                gift_invoice_id.sale_line_id.write({
                                    'remaining_gift_amount': 0.0})
                else:
                    # search Credit Card product in Invoice line
                    gift_invoice_id = self.env['account.invoice.line'].search([
                        ('invoice_id', '=', invoice.id),
                        ('gift_flag', '=', True)])
                    remaining_gift_amount =\
                        gift_invoice_id.sale_line_id.remaining_gift_amount
                    if gift_invoice_id and remaining_gift_amount > 0.0:
                        # check remaining sc amount with invoice non sc/gc
                        # amount total
                        if remaining_gift_amount >= product_total:
                            # update invoice line with new calculation amount
                            gift_invoice_id.write({
                                'price_unit': -(product_total)})
                            # update sale line remaining Store credit amount
                            gift_invoice_id.sale_line_id.write({
                                'remaining_gift_amount':
                                    remaining_gift_amount - product_total})
                        else:
                            # update invoice line with new calculation amount
                            gift_invoice_id.write({
                                'price_unit': -(remaining_gift_amount)})
                            # update sale line remaining Store credit amount
                            gift_invoice_id.sale_line_id.write({
                                'remaining_gift_amount': 0.0})
            elif invoice.amount_total < 0.0 and\
                    invoice.type == 'out_invoice' or\
                    invoice.sale_gift_lines >= 1 and\
                    invoice.inv_gift_lines >= 1:
                # search Credit Card product in Invoice line
                gift_invoice_id = self.env['account.invoice.line'].search(
                    [('invoice_id', '=', invoice.id),
                     ('gift_flag', '=', True)])
                remaining_gift_amount =\
                    gift_invoice_id.sale_line_id.remaining_gift_amount
                if gift_invoice_id and remaining_gift_amount > 0.0:
                    # check remaining sc amount with invoice non sc/gc
                    # amount total
                    if remaining_gift_amount >= product_total:
                        # update invoice line with new calculation amount
                        gift_invoice_id.write({'price_unit': -(product_total)})
                        # update sale line remaining Store credit amount
                        gift_invoice_id.sale_line_id.write({
                            'remaining_gift_amount':
                                remaining_gift_amount - product_total})
                    else:
                        # update invoice line with new calculation amount
                        gift_invoice_id.write({
                            'price_unit': -(remaining_gift_amount)})
                        # update sale line remaining Store credit amount
                        gift_invoice_id.sale_line_id.write({
                            'remaining_gift_amount': 0.0})
            else:
                if self.sale_id:
                    # set total for Store credit product
                    sale_line_sc_id = self.env['sale.order.line'].search([
                        ('order_id', '=', self.sale_id.id),
                        ('sc_flag', '=', True)])
                    # set total for Store credit product
                    sale_sc_total = sale_line_sc_id.remaining_sc_amount
                    # set total for Gift card product
                    sale_line_gift_id = self.env['sale.order.line'].search([
                        ('order_id', '=', self.sale_id.id),
                        ('gift_flag', '=', True)])
                    # set total for Gift card product
                    sale_gift_total = sale_line_gift_id.remaining_gift_amount
                    if sale_sc_total > 0.0:
                        if sale_sc_total >= product_total:
                            # create Store credit product
                            self._create_store_credit_product(
                                sale_line_sc_id, product_total)
                            # update Store credit remaining amount
                            sale_line_sc_id.write({
                                'remaining_sc_amount':
                                    sale_line_sc_id.remaining_sc_amount -
                                    product_total})
                        else:
                            remaining_product_total = \
                                product_total - \
                                sale_line_sc_id.remaining_sc_amount
                            # create Store credit product
                            self._create_store_credit_product(
                                sale_line_sc_id,
                                sale_line_sc_id.remaining_sc_amount)
                            # update Store credit remaining amount
                            sale_line_sc_id.write({
                                'remaining_sc_amount': 0.0})
                            if sale_gift_total >= remaining_product_total:
                                if self.sale_gift_lines >= 1:
                                    # create Gift card product
                                    self._create_gift_card_product(
                                        sale_line_gift_id,
                                        remaining_product_total)
                                    # update Gift card remaining amount
                                    remaining_gift_amount = \
                                        sale_line_gift_id.remaining_gift_amount
                                    sale_line_gift_id.write({
                                        'remaining_gift_amount':
                                            remaining_gift_amount -
                                            remaining_product_total})
                            else:
                                if self.sale_gift_lines >= 1 and \
                                        sale_gift_total > 0.0:
                                    # create Gift card product
                                    self._create_gift_card_product(
                                        sale_line_gift_id,
                                        sale_gift_total)
                                    # update Gift card remaining amount
                                    sale_line_gift_id.write({
                                        'remaining_gift_amount': 0.0})
                    else:
                        if sale_gift_total >= product_total:
                            # create Gift card product
                            self._create_gift_card_product(
                                sale_line_gift_id, product_total)
                            # update Gift card remaining amount
                            sale_line_gift_id.write({
                                'remaining_gift_amount':
                                    sale_line_gift_id.remaining_gift_amount -
                                    product_total})
                        else:
                            if self.sale_gift_lines >= 1 and \
                                    sale_gift_total > 0.0:
                                # create Gift card product
                                self._create_gift_card_product(
                                    sale_line_gift_id,
                                    sale_gift_total)
                                # update Gift card remaining amount
                                sale_line_gift_id.write({
                                    'remaining_gift_amount': 0.0})
        return True
