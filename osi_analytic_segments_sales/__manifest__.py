# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Analytic Segments Sales",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
	"description": "Additional segments for analytic accounts for Sales",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "images": [],
    "depends": [
        "sale",
        "stock_account",
        "sale_management",
        "osi_analytic_segments",
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
