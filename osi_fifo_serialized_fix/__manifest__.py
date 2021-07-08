# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI FIFO Serialized Product Fix",
    "summary": """Properly handle Inventory Valuation with Serialized and Lot Tracked products""",
    "version": "13.0.1.0.0",
    "author": "Open Source Integrators",
    "category": "Accounting",
    "depends": ["stock_account"],
    "data": ["views/stock_valuation_layer.xml"],
    "maintainers": ["osi-scampbell"],
    "installable": True,
}
