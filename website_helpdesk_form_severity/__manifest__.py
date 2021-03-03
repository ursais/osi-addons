# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Portal add Severity field",
    "summary": """Add severity field to Helpdesk Portal form.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": """Open Source Integrators, Serpent Consulting Services""",
    "category": "Helpdesk",
    "maintainers": ["Open Source Integrators"],
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "helpdesk_severity",
        "website_helpdesk_form",
    ],
    "data": [
        "data/website_helpdesk.xml",
        "views/helpdesk_template.xml"
    ],
    "installable": True,
}
