# Copyright (C) 2023 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": " Manufacturing - Clean Components on BoM",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Adds Clean Components action to BoM's to remove archived items.",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "depends": [
        "mrp",
        "product_configurator_mrp_component",
    ],
    "data": [
        "data/ir_actions_server.xml",
    ],
    "application": True,
    "maintainers": ["ursais"],
}
