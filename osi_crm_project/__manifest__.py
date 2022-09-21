# Copyright (C) 2022 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "CRM - Project",
    "version": "14.0.1.0.0",
    "category": "Hidden",
    "license": "AGPL-3",
    "maintainers": "Open Source Integrators",
    "depends": ["crm", "project"],
    "summary": """
     Creates and links tasks from the opportunity""",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "data": [
        "security/ir.model.access.csv",
        "views/crm_views.xml",
        "views/task_views.xml",
        "wizard/crm_task_view.xml",
    ],
    "installable": True,
    "application": False,
}
