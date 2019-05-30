# Copyright (C) 2019 - TODAY, Open Source Integrators
# # License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    'name': 'Helpdesk Stage Server Action',
    'summary': 'Add Server Actions based on Helpdesk Stage',
    'version': '12.0.1.0.0',
    'category': 'Helpdesk',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk',
    ],
    'data': [
        'data/ir_servers_action.xml',
        'views/helpdesk_stage.xml'
    ],
    'installable': True,
    'license': 'LGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'wolfhall',
        'osi-scampbell',
        'max3903',
    ],
}
