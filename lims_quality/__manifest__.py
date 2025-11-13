# Copyright (C) 2025 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Laboratory Information Management System (LIMS) Quality",
    "summary": "Integrate LIMS with Odoo Quality module",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Quality",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-lims",
    "depends": ["lims", "quality_control"],
    "data": [
        "views/lims_order_test_view.xml",
        "views/lims_quality_menus.xml",
    ],
    "application": False,
    "development_status": "Beta",
    "maintainers": ["max3903", "jasiel-osi", "Nikul-OSI"],
}
