# Copyright (C) 2020 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Helpdesk Timesheet - Field Service',
    'summary': 'Create FSM Orders and Timesheet from Helpdesk Ticket',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'category': 'Helpdesk',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk_timesheet',
        'helpdesk_fieldservice',
    ],
    'data': [
        'views/helpdesk_ticket.xml',
    ],
    'auto_install': True,
}
