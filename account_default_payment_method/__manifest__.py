# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Default Payment Information',
    'version': '12.0.1.0.0',
    'author': 'Open Source Integrators',
    'summary': 'Store and use the default payment information of a partner',
    'category': 'Customers',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'purchase',
        'sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/account_invoice.xml',
    ],
    'development_status': 'Beta',
    'maintainers': ['max3903'],
}
