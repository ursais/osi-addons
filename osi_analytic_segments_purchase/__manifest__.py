# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'OSI Analytic Segments Purchase',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
	'summary': 'Additional analytic segments in Purchase',
    'author': 'Open Source Integrators',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'category': 'Analytic Accounting',
    'depends': [
        'account',
        'purchase',
        'osi_analytic_segments',
    ],
    'data': [
        'views/purchase_order_view.xml',
    ],
    'auto_install': False,
    'application': False,
}
