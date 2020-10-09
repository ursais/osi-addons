# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "OSI Board Company",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainers": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Employee",
    "depends": ["osi_board_employee"],
    "data": [
        "security/ir.model.access.csv",
        "views/company_dashboard.xml",
        "views/company_template_views.xml",
    ],
    "external_dependencies": {
        'python': ["numpy"],
    },
    "qweb": ["static/src/xml/company_dashboard_template.xml"],
    "installable": True,
    "application": True,
}
