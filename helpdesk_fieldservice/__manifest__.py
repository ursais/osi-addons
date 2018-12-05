# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Helpdesk Fieldservice",
    "summary": "Create service requests from a ticket",
    "version": "11.0.1.0.0",
    "license": "LGPL-3",
    "author": "Open Source Integrators",
    "category": "Helpdesk",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "helpdesk",
        "fieldservice",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/helpdesk_ticket_views.xml",
        "views/fsm_order_views.xml",
    ],
    "installable": True,
}
