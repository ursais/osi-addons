# Copyright (c) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    committed_amount = fields.Float(
        compute="_compute_committ_uncommitt_amount", string="Committed Amount"
    )
    uncommitted_amount = fields.Float(
        compute="_compute_committ_uncommitt_amount", string="Uncommitted Amount"
    )
    over_budget = fields.Boolean(compute="_compute_over_budget", string="Over Budget")

    def _compute_committ_uncommitt_amount(self):
        purchase_line_obj = self.env["purchase.order.line"]
        company_currency = self.company_id.currency_id
        for budget_line in self:
            commit_domain = [
                ("date_order", ">=", budget_line.date_from),
                ("date_order", "<=", budget_line.date_to),
                ("order_id.state", "in", ("purchase", "done")),
                "|",
                ("account_analytic_id", "=", budget_line.analytic_account_id.id),
                ("analytic_tag_ids", "in", budget_line.analytic_tag_id.ids),
                "|",
                (
                    "product_id.property_account_expense_id",
                    "in",
                    budget_line.general_budget_id.account_ids.ids,
                ),
                (
                    "product_id.categ_id.property_account_expense_categ_id",
                    "in",
                    budget_line.general_budget_id.account_ids.ids,
                ),
            ]
            po_lines_commimt = purchase_line_obj.search(commit_domain)
            if budget_line.crossovered_budget_id.amount_include_tax:
                budget_line.committed_amount = -sum(
                    [
                        line.currency_id._convert(
                            line.price_unit,
                            company_currency,
                            self.company_id,
                            line.date_order,
                            round=False,
                        )
                        * (line.product_qty - line.qty_invoiced)
                        + line.currency_id._convert(
                            line.price_tax,
                            company_currency,
                            self.company_id,
                            line.date_order,
                            round=False,
                        )
                        for line in po_lines_commimt
                    ]
                )
            else:
                budget_line.committed_amount = -sum(
                    [
                        line.currency_id._convert(
                            line.price_unit,
                            company_currency,
                            self.company_id,
                            line.date_order,
                            round=False,
                        )
                        * (line.product_qty - line.qty_invoiced)
                        for line in po_lines_commimt
                    ]
                )
            uncommit_domain = [
                ("date_order", ">=", budget_line.date_from),
                ("date_order", "<=", budget_line.date_to),
                ("order_id.state", "not in", ("purchase", "done", "cancel")),
                "|",
                ("account_analytic_id", "=", budget_line.analytic_account_id.id),
                ("analytic_tag_ids", "in", budget_line.analytic_tag_id.ids),
                "|",
                (
                    "product_id.property_account_expense_id",
                    "in",
                    budget_line.general_budget_id.account_ids.ids,
                ),
                (
                    "product_id.categ_id.property_account_expense_categ_id",
                    "in",
                    budget_line.general_budget_id.account_ids.ids,
                ),
            ]
            po_lines_uncommit = purchase_line_obj.search(uncommit_domain)
            if budget_line.crossovered_budget_id.amount_include_tax:
                budget_line.uncommitted_amount = -sum(
                    [
                        line.currency_id._convert(
                            line.price_subtotal,
                            company_currency,
                            self.company_id,
                            line.date_order,
                            round=False,
                        )
                        + line.currency_id._convert(
                            line.price_tax,
                            company_currency,
                            self.company_id,
                            line.date_order,
                            round=False,
                        )
                        for line in po_lines_uncommit
                    ]
                )
            else:
                budget_line.uncommitted_amount = -sum(
                    [
                        line.currency_id._convert(
                            line.price_subtotal,
                            company_currency,
                            self.company_id,
                            line.date_order,
                            round=False,
                        )
                        for line in po_lines_uncommit
                    ]
                )

    def _compute_over_budget(self):
        for rec in self:
            rec.over_budget = False
            if (
                abs(rec.practical_amount)
                + abs(rec.committed_amount)
                + abs(rec.uncommitted_amount)
            ) > abs(rec.planned_amount):
                rec.over_budget = True
