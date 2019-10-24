# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Scrap Reason Code",
    "summary": "Provide a user-defined list of scrapping reasons",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Inventory",
    "depends": [
        "account",
        "purchase",
        "sales_team",
        "stock",
        "hr"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/reason_code_view.xml",
        "views/stock_scrap_views.xml",
        "views/stock_move_views.xml",
    ],
    "application": False,
}
