# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Konos
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Helpdesk Motive",
    "version": "12.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Keep the motive",
    "author": "Konos, "
              "Open Source Integrators, ",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "helpdesk",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/helpdesk_ticket_motive.xml',
        'views/helpdesk_ticket.xml',
    ],
    "application": False,
    "development_status": "Stable",
    "maintainers": [
        "nelsonramirezs",
        "max3903",
    ],
}
