# Copyright (C) 2020 Open Source Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, models
from odoo.osv import expression
from odoo.tools.misc import format_date


class AccountBankReconciliationReport(models.AbstractModel):
    _name = "account.bank.reconciled.report"
    _description = "Bank Reconciled Report"
    _inherit = "account.report"

    filter_date = {"date": "", "filter": "today"}

    line_number = 0

    def _get_columns_name(self, options):
        return [
            {"name": ""},
            {"name": _("Date")},
            {"name": _("Amount"), "class": "number"},
            {"name": _("Memo")},
            {"name": _("Reference")},
        ]

    def _add_title_line(self, options, title, amount=None, level=0, date=False):
        self.line_number += 1
        line_currency = self.env.context.get("line_currency", False)
        return {
            "id": "line_" + str(self.line_number),
            "name": title,
            "columns": [
                {"name": date and format_date(self.env, date) or "", "class": "date"},
                {"name": amount and self.format_value(amount, line_currency)},
                {"name": ""},
                {"name": ""},
            ],
            "level": level,
        }

    def _add_total_line(self, amount):
        self.line_number += 1
        line_currency = self.env.context.get("line_currency", False)
        return {
            "id": "line_" + str(self.line_number),
            "name": _("Total Virtual GL Balance"),
            "columns": [
                {"name": "", "class": "date"},
                {"name": self.format_value(amount, line_currency)},
                {"name": ""},
                {"name": ""},
            ],
            "level": 1,
            "class": "total",
        }

    def _add_bank_statement_line(self, line, amount):
        name = line.name
        line_currency = self.env.context.get("line_currency", False)
        if line.journal_entry_ids:
            for entry_id in line.journal_entry_ids:
                if entry_id.payment_id:
                    return {
                        "id": str(line.id),
                        "caret_options": "account.bank.statement.line",
                        "model": "account.bank.statement.line",
                        "name": len(name) >= 75 and name[0:70] + "..." or name,
                        "columns": [
                            {"name": format_date(self.env, line.date), "class": "date"},
                            {"name": self.format_value(amount, line_currency)},
                            {
                                "name": line.journal_entry_ids[
                                    0
                                ].payment_id.communication
                            },
                            {"name": line.ref},
                        ],
                        "class": "o_account_reports_level3",
                    }
        return {
            "id": str(line.id),
            "caret_options": "account.bank.statement.line",
            "model": "account.bank.statement.line",
            "name": len(name) >= 75 and name[0:70] + "..." or name,
            "columns": [
                {"name": format_date(self.env, line.date), "class": "date"},
                {"name": self.format_value(amount, line_currency)},
                {"name": ""},
                {"name": line.ref},
            ],
            "class": "o_account_reports_level3",
        }

    def print_pdf(self, options):
        options["active_id"] = self.env.context.get("active_id")
        return super(AccountBankReconciliationReport, self).print_pdf(options)

    def print_xlsx(self, options):
        options["active_id"] = self.env.context.get("active_id")
        return super(AccountBankReconciliationReport, self).print_xlsx(options)

    @api.model
    def _get_bank_rec_report_data(self, options, line_id=None):
        # General data + setup
        rslt = {}

        journal_id = self._context.get("active_id") or options.get("active_id")
        journal = self.env["account.journal"].browse(journal_id)
        selected_companies = self.env["res.company"].browse(
            self.env.context["company_ids"]
        )

        rslt["use_foreign_currency"] = (
            journal.currency_id != journal.company_id.currency_id
            if journal.currency_id
            else False
        )
        rslt["account_ids"] = list(
            {
                journal.default_debit_account_id.id,
                journal.default_credit_account_id.id,
            }
        )
        rslt["line_currency"] = (
            journal.currency_id if rslt["use_foreign_currency"] else False
        )
        self = self.with_context(line_currency=rslt["line_currency"])
        lines_already_accounted = self.env["account.move.line"].search(
            [
                ("account_id", "in", rslt["account_ids"]),
                ("date", "<=", self.env.context["date_to"]),
                ("company_id", "in", self.env.context["company_ids"]),
            ]
        )
        rslt["odoo_balance"] = sum(
            [
                line.amount_currency if rslt["use_foreign_currency"] else line.balance
                for line in lines_already_accounted
            ]
        )

        # Payments reconciled with a bank statement line
        aml_domain = [
            ("account_id", "in", rslt["account_ids"]),
            "|",
            ("statement_line_id", "=", False),
            ("statement_line_id.date", ">", self.env.context["date_to"]),
            ("user_type_id.type", "=", "liquidity"),
            ("full_reconcile_id", "!=", False),
            ("date", "<=", self.env.context["date_to"]),
        ]
        companies_unreconciled_selection_domain = []
        for company in selected_companies:
            company_domain = [("company_id", "=", company.id)]
            if company.account_bank_reconciliation_start:
                company_domain = expression.AND(
                    [
                        company_domain,
                        [("date", ">=", company.account_bank_reconciliation_start)],
                    ]
                )
            companies_unreconciled_selection_domain = expression.OR(
                [companies_unreconciled_selection_domain, company_domain]
            )
        aml_domain += companies_unreconciled_selection_domain

        move_lines = self.env["account.move.line"].search(aml_domain)

        if move_lines:
            rslt["reconciled_pmts"] = move_lines

        # Payments not reconciled with a bank statement line
        aml_domain2 = [
            ("account_id", "in", rslt["account_ids"]),
            "|",
            ("statement_line_id", "=", False),
            ("statement_line_id.date", ">", self.env.context["date_to"]),
            ("user_type_id.type", "=", "liquidity"),
            ("full_reconcile_id", "=", False),
            ("date", "<=", self.env.context["date_to"]),
        ]

        companies_unreconciled_selection_domain = []
        for company in selected_companies:
            company_domain = [("company_id", "=", company.id)]
            if company.account_bank_reconciliation_start:
                company_domain = expression.AND(
                    [
                        company_domain,
                        [("date", ">=", company.account_bank_reconciliation_start)],
                    ]
                )
            companies_unreconciled_selection_domain = expression.OR(
                [companies_unreconciled_selection_domain, company_domain]
            )
        aml_domain2 += companies_unreconciled_selection_domain

        move_lines2 = self.env["account.move.line"].search(aml_domain2)

        if move_lines2:
            rslt["not_reconciled_pmts"] = move_lines2

        # Bank statement lines reconciled with a payment
        rslt["reconciled_st_positive"] = self.env["account.bank.statement.line"].search(
            [
                ("statement_id.journal_id", "=", journal_id),
                ("date", "<=", self.env.context["date_to"]),
                ("journal_entry_ids", "!=", False),
                ("amount", ">", 0),
                ("company_id", "in", self.env.context["company_ids"]),
            ]
        )

        rslt["reconciled_st_negative"] = self.env["account.bank.statement.line"].search(
            [
                ("statement_id.journal_id", "=", journal_id),
                ("date", "<=", self.env.context["date_to"]),
                ("journal_entry_ids", "!=", False),
                ("amount", "<", 0),
                ("company_id", "in", self.env.context["company_ids"]),
            ]
        )

        # Bank statement lines not reconciled with a payment
        rslt["not_reconciled_st_positive"] = self.env[
            "account.bank.statement.line"
        ].search(
            [
                ("statement_id.journal_id", "=", journal_id),
                ("date", "<=", self.env.context["date_to"]),
                ("journal_entry_ids", "=", False),
                ("amount", ">", 0),
                ("company_id", "in", self.env.context["company_ids"]),
            ]
        )

        rslt["not_reconciled_st_negative"] = self.env[
            "account.bank.statement.line"
        ].search(
            [
                ("statement_id.journal_id", "=", journal_id),
                ("date", "<=", self.env.context["date_to"]),
                ("journal_entry_ids", "=", False),
                ("amount", "<", 0),
                ("company_id", "in", self.env.context["company_ids"]),
            ]
        )

        # Final
        last_statement = self.env["account.bank.statement"].search(
            [
                ("journal_id", "=", journal_id),
                ("date", "<=", self.env.context["date_to"]),
                ("company_id", "in", self.env.context["company_ids"]),
            ],
            order="date desc, id desc",
            limit=1,
        )
        rslt["last_st_balance"] = last_statement.balance_end
        rslt["last_st_end_date"] = last_statement.date

        return rslt

    @api.model
    def _get_amount(self, line, report_data):
        if report_data["use_foreign_currency"]:
            if line.currency_id == report_data["line_currency"]:
                return line.amount_currency
            else:
                return line.currency_id._convert(
                    line.amount_currency,
                    report_data["line_currency"],
                    self.env.user.company_id,
                    line.date,
                )
        else:
            return line.balance

    @api.model
    def _get_lines(self, options, line_id=None):
        # Fetch data
        report_data = self._get_bank_rec_report_data(options, line_id)
        self = self.with_context(line_currency=report_data["line_currency"])

        # Compute totals
        unrec_tot = sum(
            [
                -(self._get_amount(aml, report_data))
                for aml in report_data.get("reconciled_pmts", [])
            ]
        )
        outstanding_plus_tot = sum(
            [
                st_line.amount
                for st_line in report_data.get("reconciled_st_positive", [])
            ]
        )
        outstanding_minus_tot = sum(
            [
                st_line.amount
                for st_line in report_data.get("reconciled_st_negative", [])
            ]
        )
        computed_stmt_balance = (
            report_data["odoo_balance"]
            + outstanding_plus_tot
            + outstanding_minus_tot
            + unrec_tot
        )
        difference = computed_stmt_balance - report_data["last_st_balance"]

        # Build report
        lines = []

        lines.append(
            self._add_title_line(
                options,
                _("Virtual GL Balance"),
                amount=None
                if self.env.user.company_id.totals_below_sections
                else computed_stmt_balance,
                level=0,
            )
        )

        gl_title = _("Current balance of account %s")
        if len(report_data["account_ids"]) > 1:
            gl_title = _("Current balance of accounts %s")

        accounts = self.env["account.account"].browse(report_data["account_ids"])
        accounts_string = ", ".join(accounts.mapped("code"))
        lines.append(
            self._add_title_line(
                options,
                gl_title % accounts_string,
                level=1,
                amount=report_data["odoo_balance"],
                date=options["date"]["date"],
            )
        )

        lines.append(self._add_title_line(options, _("Operations to Process"), level=1))

        if report_data.get("not_reconciled_st_positive") or report_data.get(
            "not_reconciled_st_negative"
        ):
            lines.append(
                self._add_title_line(
                    options,
                    _(
                        "Uneconciled Bank \
                                           Statement Lines"
                    ),
                    level=2,
                )
            )
            for line in report_data.get("not_reconciled_st_positive", []):
                lines.append(self._add_bank_statement_line(line, line.amount))

            for line in report_data.get("not_reconciled_st_negative", []):
                lines.append(self._add_bank_statement_line(line, line.amount))

        if report_data.get("reconciled_st_positive") or report_data.get(
            "reconciled_st_negative"
        ):
            lines.append(
                self._add_title_line(
                    options,
                    _(
                        "Reconciled Bank \
                                           Statement Lines"
                    ),
                    level=2,
                )
            )
            for line in report_data.get("reconciled_st_positive", []):
                lines.append(self._add_bank_statement_line(line, line.amount))

            for line in report_data.get("reconciled_st_negative", []):
                lines.append(self._add_bank_statement_line(line, line.amount))

        if report_data.get("not_reconciled_pmts"):
            lines.append(
                self._add_title_line(
                    options,
                    _(
                        "Validated Payments \
                                            Not Linked with a Bank \
                                            Statement Line"
                    ),
                    level=2,
                )
            )
            for line in report_data["not_reconciled_pmts"]:
                self.line_number += 1
                line_description = line_title = line.ref
                if (
                    line_description
                    and len(line_description) > 70
                    and not self.env.context.get("print_mode")
                ):
                    line_description = line.ref[:65] + "..."
                lines.append(
                    {
                        "id": str(line.id),
                        "name": line.name,
                        "columns": [
                            {"name": format_date(self.env, line.date)},
                            {
                                "name": line_description,
                                "title": line_title,
                                "style": "display:block;",
                            },
                            {
                                "name": self.format_value(
                                    -self._get_amount(line, report_data),
                                    report_data["line_currency"],
                                )
                            },
                        ],
                        "class": "o_account_reports_level3",
                        "caret_options": "account.payment",
                    }
                )

        if report_data.get("reconciled_pmts"):
            lines.append(
                self._add_title_line(
                    options,
                    _(
                        "Validated Payments Linked \
                            with a Bank Statement Line"
                    ),
                    level=2,
                )
            )
            for line in report_data["reconciled_pmts"]:
                self.line_number += 1
                line_description = line_title = line.ref
                if (
                    line_description
                    and len(line_description) > 70
                    and not self.env.context.get("print_mode")
                ):
                    line_description = line.ref[:65] + "..."
                lines.append(
                    {
                        "id": str(line.id),
                        "name": line.name,
                        "columns": [
                            {"name": format_date(self.env, line.date)},
                            {
                                "name": line_description,
                                "title": line_title,
                                "style": "display:block;",
                            },
                            {
                                "name": self.format_value(
                                    -self._get_amount(line, report_data),
                                    report_data["line_currency"],
                                )
                            },
                        ],
                        "class": "o_account_reports_level3",
                        "caret_options": "account.payment",
                    }
                )

        if self.env.user.company_id.totals_below_sections:
            lines.append(self._add_total_line(computed_stmt_balance))

        lines.append(
            self._add_title_line(
                options,
                _(
                    "Last Bank Statement \
                                            Ending Balance"
                ),
                level=0,
                amount=report_data["last_st_balance"],
                date=report_data["last_st_end_date"],
            )
        )
        last_line = self._add_title_line(
            options, _("Unexplained Difference"), level=0, amount=difference
        )
        last_line["title_hover"] = _(
            """Difference between Virtual \
                                     GL Balance and Last Bank Statement \
                                     Ending Balance.\n
                                     If non-zero, it could be due to
                                     1) some bank statements being not yet \
                                     encoded into Odoo
                                     2) payments double-encoded"""
        )
        line_currency = self.env.context.get("line_currency", False)
        if self.env.context.get("no_format"):
            last_line["columns"][-1]["title"] = self.format_value(
                computed_stmt_balance, line_currency
            ) - self.format_value(report_data["last_st_balance"], line_currency)
        else:
            last_line["columns"][-1]["title"] = (
                self.format_value(computed_stmt_balance, line_currency)
                + " - "
                + self.format_value(report_data["last_st_balance"], line_currency)
            )
        lines.append(last_line)

        return lines

    @api.model
    def _get_report_name(self):
        journal_id = self._context.get("active_id")
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            return _("Bank Reconciliation") + ": " + journal.name
        return _("Bank Reconciliation")
