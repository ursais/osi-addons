# Copyright 2024 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Stock Request Stage",
    "version": "17.0.1.0.0",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/stock-logistics-request",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "summary": "Adds the possibility to manage stock requests by stages",
    "depends": ["stock_request"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_request_stage_views.xml",
        "views/stock_request_views.xml",
        "views/stock_request_menu.xml",
    ],
    "installable": True,
    "application": False,
}
