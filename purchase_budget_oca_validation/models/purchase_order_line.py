# Copyright (c) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_budget_lines(self):
        return self.env["crossovered.budget.lines"].search(
            [
                ("date_from", "<=", self.date_order),
                ("date_to", ">=", self.date_order),
                ("crossovered_budget_id.state", "=", "validate"),
                "|",
                ("analytic_account_id", "=", self.account_analytic_id.id),
                ("analytic_tag_id", "in", self.analytic_tag_ids.ids),
                "|",
                (
                    "general_budget_id.account_ids",
                    "in",
                    self.product_id.property_account_expense_id.ids,
                ),
                (
                    "general_budget_id.account_ids",
                    "in",
                    self.product_id.categ_id.property_account_expense_categ_id.ids,
                ),
            ]
        )
