# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Scrap Reason Code",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
	"description": """
    Reason code for scrapping.
    """,
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Analytic Accounting",
    "images": [],
    "depends": [
        "account",
        "purchase",
        "sales_team",
        "stock",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/reason_code_view.xml",
        "views/stock_scrap_views.xml",
        "views/stock_move_views.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
