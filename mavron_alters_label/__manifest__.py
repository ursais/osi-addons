# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Mavron Alters Label",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "summary": " Creates alters labels on sales orders.",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "depends": ["fleet", "sale"],
    "data": [
        "views/fleet_vehicle_views.xml",
        "views/sale_order_views.xml",
        "views/vehicle_label.xml",
    ],
    "application": False,
    "maintainers": ["opensourceintegrators"],
}
