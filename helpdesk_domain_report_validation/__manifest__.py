# Copyright (C) 2025 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Helpdesk Domain Report Validation",
    "version": "18.0.1.0.0",
    "category": "Helpdesk",
    "license": "LGPL-3",
    "summary": """Validates domain-based reports submitted to helpdesk and filters
    false positives from email security services like Mimecast.""",
    "author": "Open Source Integrators",
    "maintainers": ["opensourceintegrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "helpdesk",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/demo_domain_reports.xml",
        "views/helpdesk_domain_report_views.xml",
        "views/helpdesk_ticket_views.xml",
    ],
    "installable": True,
}
