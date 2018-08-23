# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools.float_utils import float_round


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('product_uom_qty', 'discount', 'discount_amt', 'price_unit',
                 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.discount_amt and line.price_unit != 0:
                discount = (100 * line.discount_amt) /\
                           (line.price_unit * line.product_uom_qty)
                line.discount = discount or 0.0
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(
                price,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    discount_amt = fields.Float(
        string='Discount',
        digits=dp.get_precision('Discount')
    )
    discount = fields.Float(
        string='Discount (%)',
        digits=(16, 12),
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    price_subtotal = fields.Monetary(
        compute='_compute_amount',
        string='Subtotal',
        readonly=True,
        store=True
    )

    @api.onchange('discount_amt')
    def onchange_discount_amt(self):
        if self.discount_amt:
            self.discount = (100 * self.discount_amt) /\
                            (self.price_unit * self.product_uom_qty) or 0.0
        return

    @api.multi
    def _prepare_invoice_line(self, qty):
        # Call super method
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        vals = {}
        if res:
            # Update Discount amt field
            if self.discount and self.discount_amt:
                # Set discount amt and quantity
                remaining_disc_amt = self.discount_amt
                remaining_qty = self.product_uom_qty
                # Browse sale order line's Invoice Lines
                for line in self.invoice_lines:
                    remaining_disc_amt -= line.discount_amt
                    remaining_qty -= line.quantity
                # Check if it's not the last invoice
                try:
                    discount_amt = remaining_disc_amt / remaining_qty * qty
                    discount = (100.00 * discount_amt) /\
                               (self.price_unit * qty) or 0.0
                    vals['discount'] = float_round(
                        discount,
                        precision_digits=self.env['decimal.precision'].
                        precision_get('Account'))
                    vals['discount_amt'] = float_round(
                        discount_amt,
                        precision_digits=self.env['decimal.precision'].
                        precision_get('Account'))
                except ZeroDivisionError:
                    vals['discount'] = 0.0
                    vals['discount_amt'] = 0.0
                # Update Invoice line values
                res.update({
                    'discount_amt': vals['discount_amt'] or 0.0,
                    'discount': vals['discount'] or 0.0})
        return res

    @api.model
    def create(self, vals):
        if 'discount_amt' in vals:
            try:
                vals['discount'] = (100 * vals['discount_amt']) /\
                                   (float(vals['price_unit']) *
                                    vals['product_uom_qty']) or 0.0
            except ZeroDivisionError:
                vals['discount'] = 0.0
        return super(SaleOrderLine, self).create(vals)
