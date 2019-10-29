# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

{
    'name': 'Payment Authorize.net Backend (Coming Soon)',
    'version': '12.0.1.0.0',
    'summary': """
Provides Authorize.net API for credit card payments in Odoo backend.
    """,
    'author': 'Sodexis, Inc<dev@sodexis.com>',
    'website': 'http://www.sodexis.com',
    'category': 'Accounting',
    'depends': [
        'payment_authorize',
        #'website_sale',
        'payment_authorize_addcard',
        'sod_sale_payment_method',
    ],
    'data': [
        #'views/templates.xml',
        'views/sale_view.xml',
        'views/payment_view.xml',
        'views/account_payment_view.xml',
        'views/account_invoice_view.xml',
        'views/account_journal_view.xml',
        'views/payment_acquirer_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'images': ['images/main_screenshot.png'],
    'price': 250.00,
    'currency': 'EUR',
    'license': 'OPL-1',
    'installable': True,
}