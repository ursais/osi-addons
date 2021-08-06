# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Scrap Reason Code Analtyic",
    "summary": "Provide a user-defined list of scrapping reasons",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Inventory",
    "depends": ["stock_analytic", "scrap_reason_code", "osi_analytic_segments_stock"],
    "data": [
        "views/reason_code_view.xml",
        "views/stock_scrap_views.xml",
    ],
    "application": False,
    "development_status": "Beta",
    "maintainers": ["bodedra"],
}
