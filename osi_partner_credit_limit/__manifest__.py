# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'OSI Partner Credit Limit',
    'version': '14.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Open Source Integrators',
    'category': 'Sales',
    'maintainer': 'Open Source Integrators',
    'summary': 'Enforce Partner Credit Limit',
    'website': 'http://www.opensourceintegrators.com',
    'depends': [
        'sale',
        'sale_stock',
        'stock',
    ],
    'data': [
        'security/osi_partner_credit_limit.xml',
        'views/res_partner.xml',
        'views/sale.xml',
        'views/stock.xml',
    ],
    'installable': True,
}
