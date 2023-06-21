# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def pre_init_hook(cr):

    # Update Existing Bank Suspense Accounts
    cr.execute(
        """UPDATE account_account SET reconcile=true WHERE id in
        (SELECT suspense_account_id FROM account_journal WHERE type='bank')"""
    )
