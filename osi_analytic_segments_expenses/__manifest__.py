# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Analytic Segments Expenses",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
	"description": "Additional segments for analytic accounts for Expenses.",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "images": [],
    "depends": [
        "osi_analytic_segments",
        "hr_expense",
    ],
    "data": [
        "views/hr_expense_views.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
