# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Credit Card Reconciliation",
    "summary": "Reconcile your credit cards",
    "version": "12.0.1.0.1",
    "license": "LGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Accounting",
    "depends": [
        'account_accountant',
        'account_payment_credit_card',
    ],
    "data": [
        "security/credit_card_reconciliation_security.xml",
        'security/ir.model.access.csv',
        "views/cc_rec_statement_view.xml",
        "views/account_move_line_view.xml",
        "report/cc_rec_statement_view.xml",
        "report/cc_rec_statement_detail.xml",
        "report/cc_rec_statement_summary.xml",
    ],
    "post_init_hook": 'post_init',
    "application": False,
    "development_status": "Beta",
    "maintainers": ["mgosai"],
}
