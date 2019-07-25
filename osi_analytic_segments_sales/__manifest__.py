# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI Analytic Segments Sales",
    "version": "12.0.1.0.1",
    "license": "LGPL-3",
    "summary": "Additional segments for analytic accounts for Sales",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "depends": [
        "stock_account",
        "sale_management",
        "osi_analytic_segments",
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
    "installable": True,
}
