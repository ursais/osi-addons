# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    """Used base method to append the payment order lines with custom domain."""
    @api.model
    def get_move_lines_for_bank_statement_line(
        self,
        st_line_id,
        partner_id=None,
        excluded_ids=None,
        search_str=False,
        offset=0,
        limit=None,
    ):
        res = super(AccountReconciliation, self).get_move_lines_for_bank_statement_line(
            st_line_id,
            partner_id=partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            offset=offset,
            limit=limit,
        )
        st_line = self.env["account.bank.statement.line"].browse(st_line_id)
        aml_accounts = [
            st_line.journal_id.default_credit_account_id.id,
            st_line.journal_id.default_debit_account_id.id,
        ]
        if partner_id is None:
            partner_id = st_line.partner_id.id

        # Prepare the domain to bring all the unreconcilied payment order lines
        domain = self._domain_move_lines_for_reconciliation_payment_order(
            st_line,
            aml_accounts,
            partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
        )
        # Find all the move line using custom domain of payment order
        aml_recs = self.env["account.move.line"].search(
            domain, offset=offset, limit=limit, order="date_maturity desc, id desc"
        )
        target_currency = (
            st_line.currency_id
            or st_line.journal_id.currency_id
            or st_line.journal_id.company_id.currency_id
        )
        #IMP
        """Append the list of prepared move lines of payment order with original
        payment move lines."""
        res += self._prepare_move_lines(
            aml_recs, target_currency=target_currency, target_date=st_line.date
        )
        return res

    @api.model
    def _domain_move_lines_for_reconciliation_payment_order(
        self, st_line, aml_accounts, partner_id, excluded_ids=None, search_str=False
    ):

        domain = [
            ("statement_line_id", "=", False),
            ("account_id", "in", aml_accounts),
            ("balance", "!=", 0.0),
        ]

        if partner_id:
            domain = expression.AND([domain, [("partner_id", "=", partner_id)]])

        if search_str:
            str_domain = self._domain_move_lines(search_str=search_str)
            str_domain = expression.OR(
                [str_domain, [("partner_id.name", "ilike", search_str)]]
            )
            domain = expression.AND([domain, str_domain])

        if excluded_ids:
            domain = expression.AND([[("id", "not in", excluded_ids)], domain])
        domain = expression.AND([domain, [("company_id", "=", st_line.company_id.id)]])

        if st_line.company_id.account_bank_reconciliation_start:
            domain = expression.AND(
                [
                    domain,
                    [
                        (
                            "date",
                            ">=",
                            st_line.company_id.account_bank_reconciliation_start,
                        )
                    ],
                ]
            )
        domain = expression.AND([domain, [("move_id.payment_order_id", "!=", None)]])
        return domain
