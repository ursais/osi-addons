# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Helpdesk - Stock',
    'summary': 'Inventory and Stock Operations for Helpdesk Tickets',
    'version': '11.0.0.1.0',
    'category': 'Helpdesk',
    'author': "Open Source Integrators",
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
    'license': 'AGPL-3',
    'maintainers': [
        'osimallen',
        'wolfhall',
        'max3903',
    ],
}
