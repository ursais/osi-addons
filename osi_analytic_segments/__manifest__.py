# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Analytic Segments",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
	"description": "Additional segments for analytic accounts",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "images": [],
    "depends": [
        'account',
        'analytic',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/analytic_segment.xml",
        "views/account_invoice_view.xml",
        "views/account_analytic_line_view.xml",
        "views/account_move_view.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
