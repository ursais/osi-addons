# Copyright (C) 2019 - TODAY, Open Source Integrators, Brian McMaster
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Subscription Suspensions',
    'summary': 'Suspend and Re-Activate your sales subscriptions',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators, Brian McMaster',
    'category': 'Sales',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'sale_subscription',
    ],
    'data': [
        'data/sale_subscription_data.xml',
        'views/sale_subscription.xml',
    ],
    'installable': True,
}
