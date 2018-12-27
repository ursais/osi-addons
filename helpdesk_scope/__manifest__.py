# Copyright (C) 2018 - TODAY, Open Source Integrators
# # License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Helpdesk Scope',
    'summary': 'Improve Helpdesk by assigneing scope',
    'version': '11.0.0.0.1',
    'category': 'Helpdesk',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_scope.xml',
        'views/helpdesk_ticket.xml',
        'views/helpdesk_ticket_type.xml',
        'views/helpdesk_team.xml'
    ],
    'installable': True,
    'license': 'LGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'wolfhall',
        'max3903',
    ],
}
