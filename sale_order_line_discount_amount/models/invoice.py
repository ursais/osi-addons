# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    discount_amt = fields.Float(
        string='Discount',
        digits=dp.get_precision('Discount')
    )
    discount = fields.Float(
        string='Discount (%)',
        digits=(16, 12)
    )

    @api.onchange('discount_amt')
    def onchange_discount_amt(self):
        if not self.discount_amt:
            self.discount = 0.00
        else:
            # Convert amount to %
            self.discount = (100 * self.discount_amt) /\
                            (self.price_unit * self.quantity)
        return
