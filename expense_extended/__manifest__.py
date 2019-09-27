# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Expense Account and Journal',
    'version': '12.0.1.0.0',
    'author': 'Open Source Integrators',
    'summary': 'Ensures that the product category account stays when an '
               'expense is submitted',
    'category': 'Human Resources',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'depends': [
        'hr_expense',
        'partner_payment_method',
    ],
    'data': [
        'views/expenses_view.xml',
    ],
    'qweb': [
    ],
    'installable': True,
}
