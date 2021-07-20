# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Helpdesk - Delivery',
    'summary': 'Select delivery methods and carriers on Helpdesk Tickets',
    'version': '12.0.1.0.0',
    'category': 'Helpdesk',
    'author': "Open Source Integrators",
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'osi_helpdesk_stock',
        'delivery',
    ],
    'data': [
        'views/helpdesk_ticket.xml',
    ],
    'installable': True,
    'auto_install': True,
    'license': 'LGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'max3903',
        'osi-scampbell'
    ],
}
