# Copyright (C) 2023 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Portal add Severity field",
    "summary": """Add severity field to Helpdesk Portal form.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": """Open Source Integrators, Serpent Consulting Services""",
    "category": "Helpdesk",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "helpdesk_severity",
        "website_helpdesk",
    ],
    "data": ["data/website_helpdesk.xml", "views/helpdesk_template.xml"],
    "installable": True,
}
