# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Analytic Account",
        help="The analytic account related to a sales order Line.",
        copy=False,
    )

    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        default_analytic_account = self.env["account.analytic.default"].account_get(
            product_id=self.product_id.id,
            partner_id=self.order_id.partner_id.id,
            # account_id=self.account_id.id,
            user_id=self.order_id.user_id.id,
            date=fields.Date.today(),
            company_id=self.company_id.id,
        )
        if default_analytic_account:
            d_id = default_analytic_account
            res.update(
                {
                    "account_analytic_id": d_id.id,
                    "analytic_segment_one_id": d_id.analytic_segment_one_id.id,
                    "analytic_segment_two_id": d_id.analytic_segment_two_id.id,
                }
            )
        return res

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            rec = self.env["account.analytic.default"].account_get(
                product_id=self.product_id.id,
                partner_id=self.order_id.partner_id.id,
                # account_id=self.account_id.id or False,
                user_id=self.env.uid,
                date=fields.Date.today(),
                company_id=self.company_id.id,
            )
            self.analytic_account_id = rec.analytic_id.id
            self.analytic_segment_one_id = rec.analytic_segment_one_id.id
            self.analytic_segment_two_id = rec.analytic_segment_two_id.id
