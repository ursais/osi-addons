# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI Analytic Sales Simple",
    "version": "12.0.1.0.1",
    "license": "LGPL-3",
    "summary": "Analytic Accounts for sale order lines",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "depends": [
        "account_analytic_default",
        "sale"
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
    "installable": True,
}
