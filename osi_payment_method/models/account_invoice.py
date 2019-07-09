# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from datetime import datetime
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    payment_method = fields.Many2one("custom.payment.method",
                                     string="Payment Method")
    current_date = fields.Date(string='Current Date',
                               copy=False,
                               help="Keep empty to use the invoice date.",
                               default=datetime.today().date(),
                               readonly=True,
                               states={'draft': [('readonly', False)]})

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.payment_method = self.partner_id.payment_method

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if self._context.get('default_payment_method', False):
            self.payment_method = self.purchase_id.payment_method.id
        return super(AccountInvoice, self).purchase_order_change()
