# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'OSI Analytic Segments Purchase',
    'version': '14.0.1.0.0',
    'license': 'LGPL-3',
    'summary': 'Additional analytic segments in Purchase',
    'author': 'Open Source Integrators',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'category': 'Analytic Accounting',
    'depends': [
        'purchase',
        'osi_analytic_segments',
    ],
    'data': [
        'views/purchase_order_view.xml',
    ],
    'installable': True,
}
