# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Helpdesk Scope',
    'summary': 'Improve Helpdesk by assigneing scope',
    'version': '11.0.0.0.1',
    'category': 'Helpdesk',
    'author': "Open Source Integrators",
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk',
    ],
    'data': [
        "views/helpdesk_scope.xml",
        "views/helpdesk_ticket.xml",
        "views/helpdesk_ticket_type.xml",
    ],
    'installable': True,
    'license': 'LGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'wolfhall',
        'max3903',
    ],
}
