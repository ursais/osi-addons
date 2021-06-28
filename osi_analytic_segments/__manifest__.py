# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI Analytic Segments",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Additional segments for analytic accounts",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Analytic Accounting",
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/analytic_segment.xml",
        "views/account_analytic_line_view.xml",
        "views/account_move_view.xml",
    ],
    "installable": True,
}
