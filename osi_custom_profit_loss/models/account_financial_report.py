# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models


class ReportAccountFinancialReport(models.Model):
    _inherit = "account.financial.html.report"

    filter_all_entries = False
    filter_hierarchy = True

    @api.model
    def _build_lines_hierarchy(
        self, options_list, financial_lines, solver, groupby_keys
    ):
        lines = []
        for financial_line in financial_lines:

            is_leaf = solver.is_leaf(financial_line)
            has_lines = solver.has_move_lines(financial_line)

            financial_report_line = self._get_financial_line_report_line(
                options_list[0], financial_line, solver, groupby_keys
            )
            if financial_line.hide_if_zero and all(
                self.env.company.currency_id.is_zero(column["no_format"])
                for column in financial_report_line["columns"]
                if "no_format" in column
            ):
                continue

            if financial_line.hide_if_empty and is_leaf and not has_lines:
                continue

            lines.append(financial_report_line)

            aml_lines = []
            if financial_line.children_ids:
                lines += self._build_lines_hierarchy(
                    options_list, financial_line.children_ids, solver, groupby_keys
                )
            elif is_leaf and financial_report_line["unfolded"]:
                solver_results = solver.get_results(financial_line)
                for (
                    groupby_id,
                    display_name,
                    results,
                ) in financial_line._compute_amls_results(
                    options_list, sign=solver_results["amls"]["sign"]
                ):
                    aml_lines.append(
                        self._get_financial_aml_report_line(
                            options_list[0],
                            financial_line,
                            groupby_id,
                            display_name,
                            results,
                            groupby_keys,
                        )
                    )
            lines += aml_lines

            if self.env.company.totals_below_sections and (
                financial_line.children_ids
                or (is_leaf and financial_report_line["unfolded"] and aml_lines)
            ):
                lines.append(
                    self._get_financial_total_section_report_line(
                        options_list[0], financial_report_line
                    )
                )
                financial_report_line["unfolded"] = True

        return lines

    @api.model
    def _build_headers_hierarchy(self, options_list, groupby_keys):
        if self._context.get("id") == 1:

            groupby_list = self._get_options_groupby_fields(options_list[0])

            keys_grouped_by_ids = [set() for gb in groupby_list]
            for key in groupby_keys:
                for i, value in enumerate(key[1:]):
                    if value is not None:
                        keys_grouped_by_ids[i].add(value)

            sorting_map = [
                {
                    i: (i, self.format_date(options))
                    for i, options in enumerate(options_list)
                }
            ]
            for groupby, ids_set in zip(groupby_list, keys_grouped_by_ids):
                groupby_field = self.env["account.move.line"]._fields[groupby]
                values_map = {None: (len(ids_set) + 1, _("Undefined"))}
                if groupby_field.relational:
                    sorted_records = self.env[groupby_field.comodel_name].search(
                        [("id", "in", tuple(ids_set))]
                    )
                    index = 0
                    for record, name_get_res in zip(
                        sorted_records, sorted_records.name_get()
                    ):
                        values_map[record.id] = (index, name_get_res[1])
                        index += 1
                else:
                    if groupby_field.name == "date":

                        def format_func(v):
                            return fields.Date.to_string(v)

                    elif groupby_field.name == "datetime":

                        def format_func(v):
                            return fields.Datetime.to_string(v)

                    else:

                        def format_func(v):
                            return v

                    for i, v in enumerate(sorted(list(ids_set))):
                        values_map[v] = (i, format_func(v))
                sorting_map.append(values_map)

            def _create_headers_hierarchy(level_keys, level=0):
                current_node = {}
                for key in level_keys:
                    current_node.setdefault(key[0], set())
                    sub_key = key[1:]
                    if sub_key:
                        current_node[key[0]].add(sub_key)
                headers = [
                    {
                        "name": sorting_map[level][key][1],
                        "colspan": len(sub_keys) or 1,
                        "children": _create_headers_hierarchy(sub_keys, level=level + 1)
                        if sub_keys
                        else None,
                        "key": key,
                        "class": "number",
                    }
                    for key, sub_keys in current_node.items()
                ]
                headers = sorted(
                    headers, key=lambda header: sorting_map[
                        level][header["key"]][0]
                )
                return headers

            level_keys = [(0,) + key[1:] for key in groupby_keys] or [(0,)]
            headers_hierarchy = _create_headers_hierarchy(set(level_keys))

            headers = [[] for i in range(len(groupby_list) + 1)]
            sorted_groupby_keys = []

            def _populate_headers(current_node, current_key, level=0):
                if current_key is None:
                    current_key = []
                headers[level] += current_node
                for header in current_node:
                    children = header.pop("children")
                    if children:
                        _populate_headers(
                            children, current_key + [header["key"]], level=level + 1
                        )
                    else:
                        sorted_groupby_keys.append(
                            tuple(current_key + [header["key"]]))

            _populate_headers(headers_hierarchy)

            for j in range(1, len(headers)):
                if not headers[j]:
                    headers[j].append(
                        {"name": "", "class": "number", "colspan": 1})

            additional_sorted_groupby_keys = []
            additional_headers = [[] for i in range(len(groupby_list) + 1)]
            for i in enumerate(options_list):
                if i == 0:
                    headers[0][0]["name"] = sorting_map[0][0][1]
                else:
                    for j in range(len(headers)):
                        if j == 0:
                            additional_headers[j].append(headers[j][-1].copy())
                        else:
                            additional_headers[j] += headers[j]
                    additional_headers[0][-1]["name"] = sorting_map[0][i][1]
                    for key in sorted_groupby_keys:
                        new_key = list(key)
                        new_key[0] = i
                        additional_sorted_groupby_keys.append(tuple(new_key))
            sorted_groupby_keys += additional_sorted_groupby_keys
            for i, headers_row in enumerate(additional_headers):
                headers[i] += headers_row

            for i in range(len(headers)):
                headers[i] = [{"name": "", "class": "number", "colspan": 1}] + headers[
                    i
                ]
            headers[0].insert(
                1, {"name": "Budget Amount", "class": "number", "colspan": 1}
            )
            headers[0].append(
                {"name": "Remaining Amount", "class": "number", "colspan": 1}
            )
            if self._display_growth_comparison(options_list[0]):
                headers[0].append(
                    {"name": "%", "class": "number", "colspan": 1})

            if self._display_debug_info(options_list[0]):
                for i in range(len(headers)):
                    if i == 0:
                        headers[i].append(
                            {
                                "template": "account_reports.cell_template_show_bug_financial_reports",
                                "style": "width: 1%; text-align: right;",
                            }
                        )
                    else:
                        headers[i].append(
                            {"name": "", "style": "width: 1%; text-align: right;"}
                        )

            return headers, sorted_groupby_keys
        else:
            return super(ReportAccountFinancialReport, self)._build_headers_hierarchy(
                options_list, groupby_keys
            )

    @api.model
    def _get_financial_line_report_line(
        self, options, financial_line, solver, groupby_keys
    ):
        if self._context.get("id") == 1:
            results = solver.get_results(financial_line)["formula"]

            is_leaf = solver.is_leaf(financial_line)
            has_lines = solver.has_move_lines(financial_line)
            has_something_to_unfold = (
                is_leaf and has_lines and bool(financial_line.groupby)
            )

            is_unfoldable = (
                has_something_to_unfold and financial_line.show_domain == "foldable"
            )

            if not has_something_to_unfold or financial_line.show_domain == "never":
                is_unfolded = False
            elif financial_line.show_domain == "always":
                is_unfolded = True
            elif (
                financial_line.show_domain == "foldable"
                and financial_line.id in options["unfolded_lines"]
            ):
                is_unfolded = True
            else:
                is_unfolded = False

            columns = []
            for key in groupby_keys:
                amount = results.get(key, 0.0)
                columns.append(
                    {
                        "name": self._format_cell_value(financial_line, amount),
                        "no_format": amount,
                        "class": "number",
                    }
                )
            columns = [{"name": "", "no_format": "",
                        "class": "number"}] + columns
            columns.append({"name": "", "no_format": "", "class": "number"})
            if self._display_growth_comparison(options):
                columns.append(
                    self._compute_growth_comparison_column(
                        options,
                        columns[0]["no_format"],
                        columns[1]["no_format"],
                        green_on_positive=financial_line.green_on_positive,
                    )
                )

            if self._display_debug_info(options):
                columns.append(
                    self._compute_debug_info_column(
                        options, solver, financial_line)
                )

            financial_report_line = {
                "id": financial_line.id,
                "name": financial_line.name,
                "level": financial_line.level,
                "class": "o_account_reports_totals_below_sections"
                if self.env.company.totals_below_sections
                else "",
                "columns": columns,
                "unfoldable": is_unfoldable,
                "unfolded": is_unfolded,
                "page_break": financial_line.print_on_new_page,
                "action_id": financial_line.action_id.id,
            }

            if (
                self.tax_report
                and financial_line.domain
                and not financial_line.action_id
            ):
                financial_report_line["caret_options"] = "tax.report.line"

            return financial_report_line
        else:
            return super(
                ReportAccountFinancialReport, self
            )._get_financial_line_report_line(
                options, financial_line, solver, groupby_keys
            )

    @api.model
    def _get_financial_aml_report_line(
        self, options, financial_line, groupby_id, display_name, results, groupby_keys
    ):
        if self._context.get("id") == 1:
            columns = []
            for key in groupby_keys:
                amount = results.get(key, 0.0)
                columns.append(
                    {
                        "name": self._format_cell_value(financial_line, amount),
                        "no_format": amount,
                        "class": "number",
                    }
                )
            total_amount = []
            if financial_line.groupby == "account_id":
                domain = [
                    ("general_budget_id.account_ids", "in", [groupby_id]),
                    ("date_from", ">=", options.get("date").get("date_from")),
                    ("date_to", "<=", options.get("date").get("date_to")),
                    ("crossovered_budget_id.state", "!=", ["draft", "cancel"]),
                ]
                if options.get("analytic_accounts"):
                    domain.append(
                        ("analytic_account_id", "=",
                         options.get("analytic_accounts"))
                    )
                crossovered_lines = self.env[
                    "crossovered.budget.lines"].search(domain)
                total_budget = 0
                for rec in crossovered_lines:
                    if rec.general_budget_id:
                        amount = rec.planned_amount / len(
                            rec.general_budget_id.account_ids
                        )
                        total_amount.append(amount)
                if total_amount:
                    total_budget = sum(total_amount)
                columns = [
                    {
                        "name": self._format_cell_value(financial_line, total_budget),
                        "no_format": total_budget,
                        "class": "number",
                    }
                ] + columns
                rem_budget = total_budget - abs(columns[1].get("no_format"))
                columns.append(
                    {
                        "name": self._format_cell_value(financial_line, rem_budget),
                        "no_format": rem_budget,
                        "class": "number",
                    }
                )
            if self._display_growth_comparison(options):
                columns.append(
                    self._compute_growth_comparison_column(
                        options,
                        columns[0]["no_format"],
                        columns[1]["no_format"],
                        green_on_positive=financial_line.green_on_positive,
                    )
                )

            if self._display_debug_info(options):
                columns.append({"name": "", "style": "width: 1%;"})
            return {
                "id": "financial_report_group_{}_{}".format(
                    financial_line.id, groupby_id
                ),
                "name": display_name,
                "level": financial_line.level + 1,
                "parent_id": financial_line.id,
                "caret_options": financial_line.groupby == "account_id"
                and "account.account"
                or financial_line.groupby,
                "columns": columns,
            }
        else:
            return super(
                ReportAccountFinancialReport, self
            )._get_financial_aml_report_line(
                options, financial_line, groupby_id, display_name, results, groupby_keys
            )
