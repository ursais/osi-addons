# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    @api.model
    def _domain_move_lines_for_reconciliation(
        self, st_line, aml_accounts, partner_id, excluded_ids=None, search_str=False
    ):
        domain = super()._domain_move_lines_for_reconciliation(
            st_line=st_line,
            aml_accounts=aml_accounts,
            partner_id=partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
        )
        # Filter with the accounts of the journal
        return expression.AND([domain, [("account_id", "in", aml_accounts)]])
