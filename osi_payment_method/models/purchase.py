# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import frozendict


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    payment_method = fields.Many2one("account.payment.method", string="Payment Method")

    @api.onchange("partner_id")
    def onchange_payment_method(self):
        self.payment_method = self.partner_id.payment_method.id or False
        return {}

    # to-do #Remove(No-need as onchange changes value)
    def action_view_invoie(self, invoices=False):
        res = super().action_view_invoice(invoices)
        ctx = dict(self._context)
        ctx.update({"default_payment_method": self.payment_method.id})
        self.env.args = frozendict(ctx)
        res["context"] = ctx
        return res


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_purchase_order(self, company_id, origins, values):
        res = super()._prepare_purchase_order(company_id, origins, values)
        values = values[0]
        partner = values["supplier"].name
        if res and partner and "payment_method" not in res:
            res.update(
                {
                    "payment_method": partner.payment_method
                    and partner.payment_method.id
                    or False
                }
            )
        return res
