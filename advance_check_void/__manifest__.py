# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Advance Check Void",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "summary": "Void History for Check Payments",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "license": "AGPL-3",
    "depends": [
        "account_check_printing",
    ],
    "data": [
        "data/payment_methods_data.xml",
        "security/ir.model.access.csv",
        "wizard/account_move_reversal_view.xml",
        "wizard/simple_void_check.xml",
        "views/account_payment_view.xml",
        "views/payment_check_history_view.xml",
    ],
    "maintainers": ["Open Source Integrators"],
    "installable": True,
    "auto_install": False,
    "application": True,
}
