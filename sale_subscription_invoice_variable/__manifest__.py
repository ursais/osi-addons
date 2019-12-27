# Copyright (C) 2019, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Subscription Variable Invoicing',
    'summary': 'Include variable consumed amount in recurring bills',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'category': 'Sales',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'sale_subscription',
    ],
    'data': [
        'views/sale_subscription_views.xml',
    ],
    'installable': True,
}
