# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'OSI Payment Method',
    'version': '12.0.1.0.1',
    'author': 'Open Source Integrators',
    'summary': 'Adds a payment method field to several models and views',
    'category': 'Customers',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'osi_vendor_reference',
    ],
    'data': [
        'views/res_partner_views.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_invoice_views.xml',
    ],
    'installable': True,
    'development_status': 'Beta',
    'maintainers': ['osimallen'],
}
