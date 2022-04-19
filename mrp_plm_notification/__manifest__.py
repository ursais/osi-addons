# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "PLM Notifications",
    "version": "14.0.1.0.0",
    "category": "Manufacturing",
    "license": "AGPL-3",
    "maintainers": "Open Source Integrators",
    "depends": ["mrp_plm"],
    "summary": "Adds email templates to ECO Stages.",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "data": [
        "data/mail_data.xml",
        "views/mrp_eco_views.xml",
    ],
    "installable": True,
    "application": False,
}
