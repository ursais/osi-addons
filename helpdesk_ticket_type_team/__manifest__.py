# Copyright (C) 2017 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Helpdesk ticket type team",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Limits the selection of helpdesk ticket types based on the team",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        # Odoo + Enterprise
        "helpdesk",
        # OCA
        # osi-addons
    ],
    "data": [
        "views/helpdesk_view.xml",
    ],
    "application": False,
    "maintainers": ["ursais"],
}
