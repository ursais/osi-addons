# -*- coding: utf-8 -*-
{
    'name': 'OnLogic Sale Lead Time - ESD Calculation',
    'version': '16.0.1.0.0',
    'category': 'Sales',
    'summary': 'Estimated Ship Date (ESD) calculation based on component availability',
    'description': """
        This module provides enhanced Estimated Ship Date (ESD) calculation
        for sales orders based on:
        - Component availability from inventory forecasts
        - Nested Bill of Materials (BoM) expansion
        - Manufacturing lead times and rush order support
        - Dynamic lead time calculation
    """,
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'sale_stock',
        'mrp',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
