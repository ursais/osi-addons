# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Sale Test Field",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "license": "LGPL-3",
    "summary": "Adds test_field to sale.order form view",
    "description": """
        This module extends the sale.order model to add a test_field (string)
        and displays it in the sale order form view.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["opensourceintegrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "sale_management",
    ],
    "data": [
        "views/sale_order_view.xml",
    ],
    "installable": True,
}
