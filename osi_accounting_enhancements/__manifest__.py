# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Supplier Invoice Customizations",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Accounting",
    "depends": ["sale", "account", "account_voucher", "purchase"],
    "data": [
        "security/security.xml",
        "views/account_invoice_view.xml",
        "views/account_voucher_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
