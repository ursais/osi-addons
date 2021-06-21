# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    payment_method = fields.Many2one("account.payment.method", string="Payment Method")
    current_date = fields.Date(
        string="Current Date",
        copy=False,
        help="Keep empty to use the invoice date.",
        default=datetime.today().date(),
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    @api.onchange("partner_id", "purchase_id")
    def onchange_payment_method(self):
        if self._context.get("default_payment_method", False):
            self.payment_method = self.purchase_id.payment_method.id or False
        else:
            self.payment_method = self.partner_id.payment_method.id or False
        return {}
