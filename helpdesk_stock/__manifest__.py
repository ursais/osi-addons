# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Helpdesk - Stock',
    'summary': 'Inventory and Stock Operations for Helpdesk Tickets',
    'version': '12.0.1.1.0',
    'category': 'Helpdesk',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'helpdesk_timesheet',
        'stock_request_direction',
        'stock_request_picking_type',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_views.xml',
        'views/stock_request.xml',
        'views/stock_request_order.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'maintainers': [
        'osimallen',
        'wolfhall',
        'max3903',
    ],
}
