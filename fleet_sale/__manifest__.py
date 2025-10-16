# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Fleet Sales",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Fleet Sales Customization - Link fleet vehicles to sale orders",
    "description": """
        This module extends the fleet management functionality by adding:
        - Vehicle field to sale orders
        - Sale order count and access from fleet vehicles
        - Integration between fleet and sales modules
    """,
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/OCA/partner-contact",
    "depends": ["fleet", "sale_management"],
    "data": [
        "views/view_fleet_vehicle.xml",
        "views/view_sale_order.xml",
    ],
    "maintainers": ["opensourceintegrators"],
    "installable": True,
    "auto_install": False,
    "application": False,
    "category": "Fleet Management",
}
