# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'MRP extended',
    'version': '8.0.1.0.0',
    'author': 'Ursa Information Systems',
    'website': 'http://www.ursainfosystems.com',
    'category': 'Manufacturing',
    'summary': 'BOM',
    'depends': [
        'product',
        'procurement',
        'stock_account',
        'resource',
        'report'
    ],
    'description': """
Key Features
------------
* Adds Quantity On Hand in BOM report.
    """,
    'data': [
        'report/mrp_report.xml',
        'views/report_mrpbomstructure_ext.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
