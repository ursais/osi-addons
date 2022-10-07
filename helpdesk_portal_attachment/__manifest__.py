# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Portal Attachments on Ticket",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": """Open Source Integrators, Serpent Consulting Services""",
    "summary": """Add multiple attachments on Portal Ticket messages.""",
    "category": "Helpdesk",
    "maintainers": ["Open Source Integrators"],
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "helpdesk",
    ],
    "data": [],
    "qweb": [
        "static/src/xml/portal_chatter.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            'helpdesk_portal_attachment/static/src/js/portal_chatter.js'
        ],
    },
    "installable": True,
}
