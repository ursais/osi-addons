# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Helpdesk Ticket Type Default Priority',
    'summary': 'Set the priority based on the type',
    'version': '11.0.0.0.1',
    'category': 'Helpdesk',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk',
    ],
    'data': [
        'views/helpdesk_ticket_type_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'maintainers': [
        'wolfhall',
        'max3903',
    ],
}
