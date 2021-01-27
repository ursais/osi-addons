# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _domain_move_lines_for_reconciliation(
        self,
        account_id,
        partner_id,
        excluded_ids=None,
        search_str=False,
        mode="rp",
    ):
        """ Return the domain for account.move.line records which can be used
            for bank statement reconciliation.

            :param aml_accounts:
            :param partner_id:
            :param excluded_ids:
            :param search_str:
            :param mode: 'rp' for receivable/payable or 'other'
        """
        domain = super()._domain_move_lines_for_reconciliation(
            account_id,
            partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            mode=mode,
        )
        # Browse journal
        if self._context.get("journal_id", False):
            acc_ids = []
            acc_move_obj = self.env["account.move.line"]
            journal = self.env["account.journal"].browse(
                self._context.get("journal_id", False)
            )
            # Get journal's default debit account
            if journal.default_debit_account_id:
                acc_ids.append(journal.default_debit_account_id.id)
            # Get journal's default credit account
            if journal.default_credit_account_id:
                acc_ids.append(journal.default_credit_account_id.id)
            acc_lines_temp = acc_move_obj.search(
                [("account_id", "in", acc_ids), ("statement_id", "=", False)]
            ).ids

            # Append additional domain to existing domain
            additional_domain = [("id", "in", acc_lines_temp)]
            domain.remove("&")
            domain.remove(("payment_id", "<>", False))
            domain = expression.AND([domain, additional_domain])
        return domain
