# -*- coding: utf-8 -*-
# Copyright 2018 Sodexis
# License OPL-1 (See LICENSE file for full copyright and licensing details).

{
    'name': "Payment Authorize.net: Add a card",
    'summary': """
        This app lets the Odoo user to add authorize.net payment details(credit-card) for a customer.
    """,
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'website': "http://www.sodexis.com",
    'author': "Sodexis, Inc <dev@sodexis.com>",
    'license': 'OPL-1',
    'depends': [
        'sale',
        'account',
        #'website_payment',
        'payment_authorize',
    ],
    'data': [
        'security/security.xml',
        #'templates/template.xml',
        'views/res_partner_view.xml',
        'views/sale_view.xml',
        'views/account_invoice_view.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'price': 49.00,
    'currency': 'EUR',
    'installable': True,
}
