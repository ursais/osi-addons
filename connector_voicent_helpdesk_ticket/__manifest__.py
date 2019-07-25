# Copyright (C) 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Voicent Helpdesk Ticket Connector',
    'version': '12.0.1.2.1',
    'license': 'LGPL-3',
    'category': 'connector',
    'author': 'Open Source Integrators',
    'summary': '''Automate calls to customers when tickets reach a stage''',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'connector_voicent',
        'helpdesk_ticket_parent',
    ],
    'external_dependencies': {
        'python': [
            'voicent',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'view/backend_voicent_call_line.xml',
        'view/backend_voicent.xml',
    ],
    'development_status': 'Beta',
    'maintainers': [
        'max3903',
    ],
}
