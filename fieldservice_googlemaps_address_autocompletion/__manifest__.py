# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Field Service - Google Maps Address Auto-completion",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Auto-complete addresses with Google Maps",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "web_view_google_map",
        "fieldservice",
    ],
    "data": [
        "views/fsm_location.xml",
        "views/res_partner.xml",
    ],
    "development_status": "Beta",
    "maintainers": [
        "osimallen",
    ],
    "installable": True,
}
