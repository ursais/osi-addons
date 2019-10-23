# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Field Service - Helpdesk - Stock',
    'summary': 'Manage material requirements from Field Service and Helpdesk',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'category': 'Field Service',
    'license': 'LGPL-3',
    'version': '12.0.1.1.0',
    'depends': [
        'fieldservice_stock',
        'helpdesk_fieldservice',
        'helpdesk_stock',
    ],
    'data': [
        'views/helpdesk_views.xml',
        'views/stock_request_order.xml',
        'views/stock_request.xml'
    ],
    'development_status': 'Beta',
    'maintainers': [
        'max3903',
        'bodedra'
    ],
    'auto_install': True,
}
