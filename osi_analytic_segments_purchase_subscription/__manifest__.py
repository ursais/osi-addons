# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Analytic Segments in Purchase Subscription',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'Additional analytic segments in purchase subscription',
    'author': 'Open Source Integrators',
    'maintainer': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'category': 'Analytic Accounting',
    'depends': [
        'purchase_subscription',
        'osi_analytic_segments',
    ],
    'data': [
        'views/purchase_subscription.xml',
    ],
    'installable': True,
}
