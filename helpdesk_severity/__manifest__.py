# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk add Severity field",
    "summary": """Add severity field to Helpdesk Tickets.""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": """Open Source Integrators, Serpent Consulting Services""",
    "category": "Helpdesk",
    "maintainers": ["Open Source Integrators"],
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "website_helpdesk_form",
    ],
    "data": [
        "views/helpdesk_ticket.xml",
    ],
    "installable": True,
}
