# Import Odoo Libs
from odoo import models


class AgedPayableCustomHandler(models.AbstractModel):
    """
    Inherit the aged payable report handler to add account filtering capabilities.
    """

    _inherit = "account.aged.payable.report.handler"

    def _get_custom_display_config(self):
        """
        Define custom display configuration for the report filters.

        Returns:
            dict: Dictionary containing template configurations.
        """
        return {
            "templates": {
                "AccountReportFilters": "ol_account_reports.AccountPayableReportFilters",
            },
        }

    def _custom_options_initializer(self, report, options, previous_options=None):
        """
        Initialize custom options for the payable report.

        Args:
            report (recordset): The report instance.
            options (dict): Current report options.
            previous_options (dict, optional): Previous report options.
            Defaults to None.
        """
        super()._custom_options_initializer(
            report, options, previous_options=previous_options
        )
        self._init_options_payable_accounts(report, options, previous_options)

    def _init_options_payable_accounts(self, report, options, previous_options=None):
        """
        Initialize the payable accounts in the report options.

        Args:
            report (recordset): The report instance.
            options (dict): Current report options.
            previous_options (dict, optional): Previous report options.
            Defaults to None.
        """
        previous_payable_accounts_ids = (
            previous_options and previous_options.get("selected_payable_accounts") or []
        )

        # Ensure IDs are integers if provided as a list
        if isinstance(previous_payable_accounts_ids, list):
            previous_payable_accounts_ids = [
                int(account) for account in previous_payable_accounts_ids
            ]

            # Fetch selected payable accounts from database
            selected_payable_accounts = (
                self.env["account.account"]
                .with_context(active_test=False)
                .search([("id", "in", previous_payable_accounts_ids)])
                or []
            )

        # Store selected payable account IDs in options
        options["selected_payable_accounts"] = (
            selected_payable_accounts
            and selected_payable_accounts.ids
            or selected_payable_accounts
        )

        # Store selected payable account names in options
        options["selected_receivable_accounts_names"] = (
            selected_payable_accounts and selected_payable_accounts.mapped("name")
        )

        account_ids = self.env["account.account"].search(
            [("account_type", "=", "liability_payable")]
        )
        options["selected_payable_accounts_ids"] = account_ids.ids

class AccountReport(models.Model):
    """
    Inherit account report to add payable account filters to reports.
    """

    _inherit = "account.report"

    def _get_options_payable_accounts_domain(self, options):
        """
        Generate domain filters based on selected payable accounts.

        Args:
            options (dict): Current report options.

        Returns:
            list: Domain filter for payable accounts.
        """
        if options.get("selected_payable_accounts", []):
            return [("account_id", "in", options.get("selected_payable_accounts", []))]
        return []

    def _get_options_domain(self, options, date_scope):
        """
        Extend the domain filters for the report with payable account conditions.

        Args:
            options (dict): Current report options.
            date_scope (str): Scope of the date filter.

        Returns:
            list: Extended domain filters.
        """
        domain = super()._get_options_domain(options, date_scope)
        domain += self._get_options_payable_accounts_domain(options)

        return domain
