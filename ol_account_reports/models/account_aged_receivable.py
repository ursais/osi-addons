# Import Odoo Libs
from odoo import api, fields, models


class AgedReceiableCustomHandler(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _get_custom_display_config(self):
        return {
            "templates": {
                "AccountReportFilters": "ol_account_reports.AccountRecivableReportFilters",
            },
        }

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(
            report, options, previous_options=previous_options
        )
        self._init_options_receivable_accounts(report, options, previous_options)

    def _init_options_receivable_accounts(self, report, options, previous_options=None):
        # selected_receivable_accounts = []
        previous_receivable_accounts_ids = (
            previous_options
            and previous_options.get("selected_receivable_accounts")
            or []
        )
        if isinstance(previous_receivable_accounts_ids, list):
            previous_receivable_accounts_ids = [
                int(account) for account in previous_receivable_accounts_ids
            ]
            selected_receivable_accounts = (
                self.env["account.account"]
                .with_context(active_test=False)
                .search([("id", "in", previous_receivable_accounts_ids)])
                or []
            )

        options["selected_receivable_accounts"] = (
            selected_receivable_accounts
            and selected_receivable_accounts.ids
            or selected_receivable_accounts
        )
        options[
            "selected_receivable_accounts_names"
        ] = selected_receivable_accounts and selected_receivable_accounts.mapped("name")


class AccountReport(models.Model):
    _inherit = "account.report"

    def _get_options_receivable_accounts_domain(self, options):
        if options.get("selected_receivable_accounts", []):
            return [
                ("account_id", "in", options.get("selected_receivable_accounts", []))
            ]
        return []

    def _get_options_domain(self, options, date_scope):
        domain = super()._get_options_domain(options, date_scope)
        domain += self._get_options_receivable_accounts_domain(options)

        return domain
