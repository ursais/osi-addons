# Copyright (C) 2026 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Stock Receipt Report",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Customize the picking report for incoming receipts with "
    "purchase-related columns and French title.",
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Inventory",
    "depends": ["stock", "purchase_stock"],
    "data": [
        "views/stock_move_line_views.xml",
        "report/report_picking_inherit.xml",
    ],
    "installable": True,
}
