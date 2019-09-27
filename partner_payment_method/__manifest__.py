# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Partner Payment Method',
    'version': '12.0.1.0',
    'author': 'Open Source Integrators',
    'summary': 'Adds a partner payment method field to models and views',
    'category': 'Contacts',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'depends': ['sale', 'purchase', 'account', 'sales_team'],
    'data': [
        'views/payment_views.xml',
        'views/res_partner.xml',
        'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/account_invoice_views.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ],
    'installable': True,
}
