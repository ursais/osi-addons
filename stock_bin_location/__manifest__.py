# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Bin Location",
    "version": "14.0.1.0.0",
    "category": "Inventory",
    "summary": """Manage bin location on serial numbers""",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": ["osi_manual_qty_reserve"],
    "data": [
        "views/stock_production_lot.xml",
        "views/stock_move_line.xml",
        "views/stock_quant.xml",
        "views/stock_move.xml",
    ],
    "maintainers": ["jantoniorivera97"],
}
