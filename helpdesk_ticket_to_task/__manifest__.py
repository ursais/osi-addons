# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Tickets to multiple tasks relationships",
    "summary": "Tickets to multiple tasks relationships",
    "version": "12.0.1.0.0",
    "license": "LGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "category": "Helpdesk",
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "helpdesk",
        "helpdesk_timesheet",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/helpdesk_ticket_views.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
}
