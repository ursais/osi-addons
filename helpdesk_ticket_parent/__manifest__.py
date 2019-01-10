# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Helpdesk Ticket Parent',
    'summary': 'Add Parent/Child relationship to Helpdesk Ticket',
    'version': '11.0.0.0.1',
    'category': 'Helpdesk',
    'author': "Open Source Integrators",
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk',
        'helpdesk_timesheet'
    ],
    'data': [
        'views/helpdesk_ticket.xml'
    ],
    'installable': True,
    'license': 'LGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'wolfhall',
        'max3903',
        'osi-scampbell'
    ],
}