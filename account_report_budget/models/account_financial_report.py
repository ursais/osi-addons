# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import ast

from odoo import _, api, models
from odoo.tools import ustr


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    filter_all_entries = False
    filter_hierarchy = True

    def _compute_growth_comparison_column_variance(self, values):
        if not values:
            return {"name": _("n/a"), "class": "number"}
        else:
            if values < 0:
                return {"name": str(values) + "%", "class": "number color-red"}
            else:
                return {"name": str(values) + "%", "class": "number color-green"}

    @api.model
    def _build_headers_hierarchy(self, options_list, groupby_keys):
        headers, sorted_groupby_keys = super(
            ReportAccountFinancialReport, self
        )._build_headers_hierarchy(options_list, groupby_keys)
        if self._context.get("id") == 1 or self.id == 1:
            if (
                options_list
                and options_list[0].get("comparison")
                and options_list[0].get("comparison").get("number_period")
            ):
                header_list = []
                period_range = (
                    options_list[0].get("comparison").get("number_period") + 1
                )
                if options_list[0].get("comparison").get("filter") == "no_comparison":
                    period_range = 1
                else:
                    header_list = [headers[0][0]]
                for rec in range(0, period_range):
                    if self._display_growth_comparison(options_list[0]):
                        headers[0].insert(
                            -2 + rec,
                            {"name": "Budget Amount", "class": "number", "colspan": 1},
                        )
                        headers[0].insert(
                            -2 + rec,
                            {
                                "name": "Budget Difference",
                                "class": "number",
                                "colspan": 1,
                            },
                        )
                        headers[0].insert(
                            -2 + rec,
                            {"name": "% Variance", "class": "number", "colspan": 1},
                        )
                        header_list = []
                    else:
                        if (
                            options_list
                            and options_list[0].get("comparison")
                            and options_list[0].get("comparison").get("filter")
                            == "no_comparison"
                        ):
                            headers[0].append(
                                {
                                    "name": "Budget Amount",
                                    "class": "number",
                                    "colspan": 1,
                                }
                            )
                            headers[0].append(
                                {
                                    "name": "Budget Difference",
                                    "class": "number",
                                    "colspan": 1,
                                }
                            )
                            headers[0].append(
                                {"name": "% Variance", "class": "number", "colspan": 1},
                            )
                            header_list = []
                        else:
                            if (
                                options_list
                                and options_list[0].get("comparison")
                                and options_list[0]
                                .get("comparison")
                                .get("number_period")
                            ):
                                header_list.append(headers[0][rec + 1])
                                header_list.append(
                                    {
                                        "name": "Budget Amount",
                                        "class": "number",
                                        "colspan": 1,
                                    }
                                )
                                header_list.append(
                                    {
                                        "name": "Budget Difference",
                                        "class": "number",
                                        "colspan": 1,
                                    }
                                )
                                header_list.append(
                                    {
                                        "name": "% Variance",
                                        "class": "number",
                                        "colspan": 1,
                                    }
                                )
                            else:
                                headers[0].insert(
                                    -1,
                                    {
                                        "name": "Budget Amount",
                                        "class": "number",
                                        "colspan": 1,
                                    },
                                )
                                headers[0].insert(
                                    -1,
                                    {
                                        "name": "Budget Difference",
                                        "class": "number",
                                        "colspan": 1,
                                    },
                                )
                                headers[0].insert(
                                    -1,
                                    {
                                        "name": "% Variance",
                                        "class": "number",
                                        "colspan": 1,
                                    },
                                )
                                header_list = []
                if header_list:
                    headers[0] = header_list
        return headers, sorted_groupby_keys

    @api.model
    def _get_financial_line_report_line(
        self, options, financial_line, solver, groupby_keys
    ):
        financial_report_line = super(
            ReportAccountFinancialReport, self
        )._get_financial_line_report_line(options, financial_line, solver, groupby_keys)
        if self._context.get("id") == 1 or self.id == 1:
            if (
                options
                and options.get("comparison")
                and options.get("comparison").get("number_period")
            ):
                period_range = options.get("comparison").get("number_period") + 1
                if options.get("comparison").get("filter") == "no_comparison":
                    period_range = 1
                column_list = []
                period = -1
                financial_line_account_value = financial_report_line["columns"].copy()
                for rec in range(0, period_range):
                    domain = (
                        financial_line.domain
                        and ast.literal_eval(ustr(financial_line.domain))
                        or []
                    )
                    total_budget = 0
                    date_from = options.get("date").get("date_from")
                    date_to = options.get("date").get("date_to")
                    if period >= 0 and options.get("comparison").get("periods")[period]:
                        date_from = (
                            options.get("comparison")
                            .get("periods")[period]
                            .get("date_from")
                        )
                        date_to = (
                            options.get("comparison")
                            .get("periods")[period]
                            .get("date_to")
                        )
                    period += 1
                    variance = 0
                    rem_budget = 0
                    total_budget = 0
                    if domain:
                        lines_ids = self.env["account.move.line"].search(domain)
                        account_ids = lines_ids.mapped("account_id")
                        for rec_account in account_ids:
                            amount_list = []
                            domain = [
                                (
                                    "general_budget_id.account_ids",
                                    "in",
                                    [rec_account.id],
                                ),
                                ("date_from", "<=", date_from),
                                ("date_to", ">=", date_to),
                                (
                                    "crossovered_budget_id.state",
                                    "in",
                                    ["validate", "done"],
                                ),
                            ]
                            if options.get("analytic_accounts"):
                                domain.append(
                                    (
                                        "analytic_account_id",
                                        "in",
                                        options.get("analytic_accounts"),
                                    )
                                )
                            crossovered_lines = self.env[
                                "crossovered.budget.lines"
                            ].search(domain)
                            for rec_lines in crossovered_lines:
                                if rec_lines.general_budget_id.account_ids:
                                    amount = rec_lines.planned_amount / len(
                                        rec_lines.general_budget_id.account_ids
                                    )
                                    amount_list.append(amount)
                            total_budget += sum(amount_list)
                        rem_budget = total_budget - abs(
                            financial_line_account_value[period].get("no_format")
                        )
                        variance = 0
                        if total_budget:
                            variance = round((rem_budget / total_budget) * 100, 2)
                    if self._display_growth_comparison(options):
                        financial_report_line["columns"].insert(
                            -2 + rec,
                            {
                                "name": domain
                                and self._format_cell_value(
                                    financial_line, total_budget
                                )
                                or "",
                                "no_format": domain and total_budget or "",
                                "class": "number",
                            },
                        )
                        financial_report_line["columns"].insert(
                            -2 + rec,
                            {
                                "name": domain
                                and self._format_cell_value(financial_line, rem_budget)
                                or "",
                                "no_format": domain and total_budget or "",
                                "class": "number",
                            },
                        )
                        financial_report_line["columns"].insert(
                            -2 + rec,
                            domain
                            and self._compute_growth_comparison_column_variance(
                                variance
                            )
                            or {"name": "", "no_format": "", "class": "number"},
                        )
                        column_list = []
                    elif (
                        options
                        and options.get("comparison")
                        and options.get("comparison").get("filter") == "no_comparison"
                    ):
                        financial_report_line["columns"].append(
                            {
                                "name": domain
                                and self._format_cell_value(
                                    financial_line, total_budget
                                )
                                or "",
                                "no_format": domain and total_budget or "",
                                "class": "number",
                            }
                        )
                        financial_report_line["columns"].append(
                            {
                                "name": domain
                                and self._format_cell_value(financial_line, rem_budget)
                                or "",
                                "no_format": domain and total_budget or "",
                                "class": "number",
                            }
                        )
                        financial_report_line["columns"].append(
                            domain
                            and self._compute_growth_comparison_column_variance(
                                variance
                            )
                            or {"name": "", "no_format": "", "class": "number"},
                        )
                        column_list = []
                    elif (
                        options
                        and options.get("comparison")
                        and options.get("comparison").get("number_period")
                    ):
                        column_list.append(financial_report_line["columns"][rec])
                        column_list.append(
                            {
                                "name": domain
                                and self._format_cell_value(
                                    financial_line, total_budget
                                )
                                or "",
                                "no_format": domain and total_budget or "",
                                "class": "number",
                            }
                        )
                        column_list.append(
                            {
                                "name": domain
                                and self._format_cell_value(financial_line, rem_budget)
                                or "",
                                "no_format": domain and total_budget or "",
                                "class": "number",
                            }
                        )
                        column_list.append(
                            domain
                            and self._compute_growth_comparison_column_variance(
                                variance
                            )
                            or {"name": "", "no_format": "", "class": "number"},
                        )
                if column_list:
                    financial_report_line["columns"] = column_list
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
        if self._context.get("id") == 1 or self.id == 1:
            if (
                options
                and options.get("comparison")
                and options.get("comparison").get("number_period")
            ):
                period_range = options.get("comparison").get("number_period") + 1
                if options.get("comparison").get("filter") == "no_comparison":
                    period_range = 1
                column_list = []
                period = -1
                financial_line_account_value = financial_line_account["columns"].copy()
                for rec in range(0, period_range):
                    amount_list = []
                    if period >= 0:
                        if options.get("comparison").get("periods")[period]:
                            date_from = (
                                options.get("comparison")
                                .get("periods")[period]
                                .get("date_from")
                            )
                            date_to = (
                                options.get("comparison")
                                .get("periods")[period]
                                .get("date_to")
                            )
                    else:
                        date_from = options.get("date").get("date_from")
                        date_to = options.get("date").get("date_to")
                    period += 1

                    if financial_line.groupby == "account_id":
                        domain = [
                            ("general_budget_id.account_ids", "in", [groupby_id]),
                            ("date_from", "<=", date_from),
                            ("date_to", ">=", date_to),
                            ("crossovered_budget_id.state", "in", ["validate", "done"]),
                        ]
                        if options.get("analytic_accounts"):
                            domain.append(
                                (
                                    "analytic_account_id",
                                    "in",
                                    options.get("analytic_accounts"),
                                )
                            )
                        crossovered_lines = self.env["crossovered.budget.lines"].search(
                            domain
                        )
                        total_budget = 0
                        for rec_lines in crossovered_lines:
                            if rec_lines.general_budget_id.account_ids:
                                amount = rec_lines.planned_amount / len(
                                    rec_lines.general_budget_id.account_ids
                                )
                                amount_list.append(amount)
                        total_budget = sum(amount_list)
                        rem_budget = total_budget - abs(
                            financial_line_account_value[period].get("no_format")
                        )
                        variance = 0
                        if total_budget:
                            variance = round((rem_budget / total_budget) * 100, 2)
                        if self._display_growth_comparison(options):
                            financial_line_account["columns"].insert(
                                -2 + rec,
                                {
                                    "name": self._format_cell_value(
                                        financial_line, total_budget
                                    ),
                                    "no_format": total_budget,
                                    "class": "number",
                                },
                            )
                            financial_line_account["columns"].insert(
                                -2 + rec,
                                {
                                    "name": self._format_cell_value(
                                        financial_line, rem_budget
                                    ),
                                    "no_format": rem_budget,
                                    "class": "number",
                                },
                            )
                            financial_line_account["columns"].insert(
                                -2 + rec,
                                self._compute_growth_comparison_column_variance(
                                    variance
                                ),
                            )
                            column_list = []
                        else:
                            if (
                                options
                                and options.get("comparison")
                                and options.get("comparison").get("filter")
                                == "no_comparison"
                            ):
                                financial_line_account["columns"].append(
                                    {
                                        "name": self._format_cell_value(
                                            financial_line, total_budget
                                        ),
                                        "no_format": total_budget,
                                        "class": "number",
                                    }
                                )
                                financial_line_account["columns"].append(
                                    {
                                        "name": self._format_cell_value(
                                            financial_line, rem_budget
                                        ),
                                        "no_format": rem_budget,
                                        "class": "number",
                                    }
                                )
                                financial_line_account["columns"].append(
                                    self._compute_growth_comparison_column_variance(
                                        variance
                                    )
                                )
                                column_list = []
                            else:
                                if (
                                    options
                                    and options.get("comparison")
                                    and options.get("comparison").get("number_period")
                                ):
                                    column_list.append(
                                        financial_line_account["columns"][rec]
                                    )
                                    column_list.append(
                                        {
                                            "name": self._format_cell_value(
                                                financial_line, total_budget
                                            ),
                                            "no_format": total_budget,
                                            "class": "number",
                                        }
                                    )
                                    column_list.append(
                                        {
                                            "name": self._format_cell_value(
                                                financial_line, rem_budget
                                            ),
                                            "no_format": rem_budget,
                                            "class": "number",
                                        }
                                    )
                                    column_list.append(
                                        self._compute_growth_comparison_column_variance(
                                            variance
                                        )
                                    )
                if column_list:
                    financial_line_account["columns"] = column_list
        return financial_line_account
