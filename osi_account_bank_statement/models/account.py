# Copyright (C) 2019, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
from odoo.osv import expression


class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def _domain_move_lines_for_reconciliation(self,
                                              st_line,
                                              aml_accounts,
                                              partner_id,
                                              excluded_ids=None,
                                              search_str=False):

        res = super(AccountReconciliation, self)\
                    ._domain_move_lines_for_reconciliation(
                    st_line=st_line,
                    aml_accounts=aml_accounts,
                    partner_id=partner_id,
                    excluded_ids=excluded_ids,
                    search_str=search_str)
        # Browse journal
        if self._context.get('journal_id', False):
            acc_ids = []
            acc_lines_temp = []
            acc_move_obj = self.env['account.move.line']
            journal = self.env['account.journal'].browse(
                                                        self._context.get
                                                        ('journal_id', False))

            if journal and journal.liability_account_id:
                # Get account lines only for liable account
                acc_ids = acc_move_obj.search(
                        [('account_id',
                         'in',
                          journal.liability_account_id.id)]).ids
            else:
                # Get debit account
                if journal.default_debit_account_id:
                    acc_ids.append(journal.default_debit_account_id.id)
                # Get credit account
                if journal.default_credit_account_id:
                    acc_ids.append(journal.default_credit_account_id.id)

            acc_lines_temp = acc_move_obj.search([('account_id',
                                                   'in',
                                                   acc_ids)]).ids

            # Append additional domain to existing domain
            additional_domain = [('id', 'in', acc_lines_temp)]
            res = expression.AND([res, additional_domain])

        return res
