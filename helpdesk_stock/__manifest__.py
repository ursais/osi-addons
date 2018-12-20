# Copyright (C) 2018 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Helpdesk - Stock',
    'summary': 'Inventory and Stock Operations for Helpdesk Tickets',
    'version': '11.0.0.1.0',
    'category': 'Helpdesk',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk_timesheet',
        'stock',
    ],
    'data': [
        'views/helpdesk_views.xml',
        'views/stock.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'maintainers': [
        'osimallen',
        'wolfhall',
        'max3903',
    ],
}
