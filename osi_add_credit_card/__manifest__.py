# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI ADD CREDIT CARD TOKEN",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "description": """
    Add Credit Card Token for Authorize.net from backend.
    """,
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Payment",
    "images": [],
    "depends": [
        'payment_authorize',
        'payment_authorize_addcard',
        'payment_authorize_backend',
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/account_payment_method.xml',
        "wizard/add_cc_token_wizard_view.xml",
        "views/partner_view.xml",
        "views/sale_view.xml",
        "views/account_invoice_view.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
