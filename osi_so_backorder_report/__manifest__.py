# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'OSI SO Backorder Report',
    'version': '12.0.0.0.1',
    'author': 'Open Source Integrators',
    'summary': 'Adds the ability to view and print a report of UIGD and Backorder quantities and values',
    'category': 'Sale',
    'maintainer': 'Open Source Integrators',
    'website': 'http://www.opensourceintegrators.com',
    'depends': ['sale','sale_stock'],
    'data': [
        'views/so_backorder_view.xml',
        'views/sale_view.xml',
        'report/so_backorder_report.xml',
        'wizard/so_backorder_wizard_view.xml',
    ],
    'qweb': [        
    ],
    'installable': True,
}
