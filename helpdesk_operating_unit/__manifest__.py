# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Helpdesk Ticket with Operating Units",
    "summary": """
        This module adds operating unit information to Helpdesk tickets.""",
    "version": "12.0.1.0.0",
    "author": "Open Source Integrators, "
    "Serpent Consulting Services Pvt. Ltd.,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Helpdesk",
    "depends": ["operating_unit", "helpdesk"],
    "license": "LGPL-3",
    "data": [
        "security/helpdesk_security.xml",
        "views/helpdesk_ticket.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": [
        "max3903",
    ],
}
