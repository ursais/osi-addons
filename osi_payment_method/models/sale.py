# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_method = fields.Many2one("account.payment.method", string="Payment Method")

    @api.onchange("partner_id")
    def onchange_payment_method(self):
        self.payment_method = self.partner_id.payment_method.id or False
        return {}

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({"payment_method": self.payment_method.id})
        return invoice_vals
