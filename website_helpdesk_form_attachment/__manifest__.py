# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Helpdesk Form",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": """Open Source Integrators,
        Serpent Consulting Services,
        Odoo Community Association (OCA)""",
    "summary": """Improve Customer Helpdesk Experience.""",
    "category": "Helpdesk",
    "maintainers": ["Open Source Integrators"],
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "website_helpdesk_form",
    ],
    "data": [
        "data/website_helpdesk.xml",
        "views/assets.xml",
        "views/helpdesk_ticket.xml",
        "views/helpdest_template.xml"
    ],
    "qweb": [
        "static/src/xml/portal_chatter.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
