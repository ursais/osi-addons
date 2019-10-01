# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Expense Account and Journal',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'summary': 'Ensures that the product category account stays when an '
               'expense is submitted',
    'category': 'Human Resources',
    'maintainer': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'hr_expense',
        'osi_payment_method',
    ],
    'data': [
        'views/expenses_view.xml',
    ],
    'installable': True,
}
