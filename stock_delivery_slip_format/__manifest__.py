# Copyright (C) 2024, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Delivery Slip Format",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    Ensures consistent delivery slip formatting with Coda Part No., Description,
    Ordered (no decimals), and Delivered (no decimals) columns across all
    delivery validation states.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Inventory",
    "depends": ["stock"],
    "data": [
        "reports/delivery_slip_report.xml",
    ],
    "installable": True,
}
