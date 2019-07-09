# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'OSI Payment Method',
    'version': '12.0.1.0.0',
    'author': 'Open Source Integrators',
    'summary': 'Adds a payment method field to several models and views',
    'category': 'Customers',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'license': 'LGPL-3',
    'depends': ['sale', 'osi_vendor_reference', ],
    'data': [
        'views/payment_views.xml',
        'views/res_partner.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_invoice_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
