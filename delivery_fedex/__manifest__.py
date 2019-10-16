# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Fedex Shipping",
    'description': "Send your shippings through Fedex and track them online",
    'category': 'Warehouse',
    'version': '12.0.1.0.0',
    'depends': ['delivery', 'mail'],
    'data': [
        'data/delivery_fedex.xml',
        'views/delivery_fedex.xml',
        'views/res_config_settings_views.xml',
    ],
    'license': 'OEEL-1',
    'uninstall_hook': 'uninstall_hook',
}
