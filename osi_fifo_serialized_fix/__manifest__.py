# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI FIFO Serialized Product Fix",
    "summary": """Properly handle Inventory Valuation
     with Serialized and Lot Tracked products""",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Accounting",
    "depends": ["stock_account", "mrp_account"],
    "data": ["views/stock_valuation_layer.xml"],
    "application": False,
    "maintainers": ["osi-scampbell", "Chanakya-OSI", "RLeeOSI", "agyamuta"],
    "installable": True,
}
