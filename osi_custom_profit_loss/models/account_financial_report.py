# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    filter_all_entries = False
    filter_hierarchy = True

    @api.model
    def _build_headers_hierarchy(self, options_list, groupby_keys):
        headers, sorted_groupby_keys = super(
            ReportAccountFinancialReport, self
        )._build_headers_hierarchy(options_list, groupby_keys)
        if self._context.get("id") == 1:
            headers[0].insert(
                1, {"name": "Budget Amount", "class": "number", "colspan": 1}
            )
            if self._display_growth_comparison(options_list[0]):
                headers[0].insert(
                    -1, {"name": "Remaining Amount", "class": "number", "colspan": 1}
                )
            else:
                headers[0].append(
                    {"name": "Remaining Amount", "class": "number", "colspan": 1}
                )
        return headers, sorted_groupby_keys

    @api.model
    def _get_financial_line_report_line(
        self, options, financial_line, solver, groupby_keys
    ):
        financial_report_line = super(
            ReportAccountFinancialReport, self
        )._get_financial_line_report_line(options, financial_line, solver, groupby_keys)
        if self._context.get("id") == 1:
            financial_report_line["columns"] = [
                {"name": "", "no_format": "", "class": "number"}
            ] + financial_report_line.get("columns")
            if self._display_growth_comparison(options):
                financial_report_line["columns"].insert(
                    -1, {"name": "", "no_format": "", "class": "number"}
                )
            else:
                financial_report_line["columns"].append(
                    {"name": "", "no_format": "", "class": "number"}
                )
        return financial_report_line

    @api.model
    def _get_financial_aml_report_line(
        self, options, financial_line, groupby_id, display_name, results, groupby_keys
    ):
        financial_line_account = super(
            ReportAccountFinancialReport, self
        )._get_financial_aml_report_line(
            options, financial_line, groupby_id, display_name, results, groupby_keys
        )
        if self._context.get("id") == 1:
            total_amount = []
            if financial_line.groupby == "account_id":
                domain = [
                    ("general_budget_id.account_ids", "in", [groupby_id]),
                    ("date_from", ">=", options.get("date").get("date_from")),
                    ("date_to", "<=", options.get("date").get("date_to")),
                    ("crossovered_budget_id.state", "not in", ["draft", "cancel"]),
                ]
                if options.get("analytic_accounts"):
                    domain.append(
                        ("analytic_account_id", "=", options.get("analytic_accounts"))
                    )
                crossovered_lines = self.env["crossovered.budget.lines"].search(domain)
                total_budget = 0
                for rec in crossovered_lines:
                    if rec.general_budget_id:
                        amount = rec.planned_amount / len(
                            rec.general_budget_id.account_ids
                        )
                        total_amount.append(amount)
                if total_amount:
                    total_budget = sum(total_amount)
                financial_line_account["columns"] = [
                    {
                        "name": self._format_cell_value(financial_line, total_budget),
                        "no_format": total_budget,
                        "class": "number",
                    }
                ] + financial_line_account["columns"]
                rem_budget = total_budget - abs(
                    financial_line_account["columns"][1].get("no_format")
                )
                if self._display_growth_comparison(options):
                    financial_line_account["columns"].insert(
                        -1,
                        {
                            "name": self._format_cell_value(financial_line, rem_budget),
                            "no_format": rem_budget,
                            "class": "number",
                        },
                    )
                else:
                    financial_line_account["columns"].append(
                        {
                            "name": self._format_cell_value(financial_line, rem_budget),
                            "no_format": rem_budget,
                            "class": "number",
                        }
                    )
            return financial_line_account
