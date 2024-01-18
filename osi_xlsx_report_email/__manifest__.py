# Copyright (C) 2021 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI Email XLSX Report Scheduler",
    "version": "14.0.1.0.0",
    "author": "Open Source Integrators",
    "summary": """Email XLSX Report Scheduler""",
    "license": "LGPL-3",
    "category": "report",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": ["stock", "web"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "data/email_template.xml",
        "views/xlsx_report_email_views.xml",
    ],
    "installable": True,
    "maintainers": ["bodedra"],
}
