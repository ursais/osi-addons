# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Payment Transaction Method Fix",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    Fix payment method assignment on payment transactions to use specific
    payment methods (Sofort, iDEAL, Card, etc.) from sale orders instead
    of generic default values.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Accounting/Payment",
    "depends": ["payment", "sale"],
    "data": [
        "views/payment_transaction_views.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "application": False,
}
