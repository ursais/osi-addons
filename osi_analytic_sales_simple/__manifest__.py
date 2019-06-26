# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Analytic Sales Simple",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
	"description": "Analytic Accounts for sale order lines",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "images": [],
    "depends": [
        "account_analytic_default",
        "account",
        "sale"
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
