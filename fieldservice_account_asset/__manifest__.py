# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Field Service - Asset',
    'summary': 'Manage your field service assets',
    'version': '12.0.1.0.0',
    'category': 'Field Service',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'fieldservice_stock',
        'agreement_serviceprofile',
        'account_asset',
    ],
    'data': [
        'data/stock_location.xml',
        'views/res_config_settings.xml',
        'views/fsm_stage_view.xml',
        'views/fsm_equipment_view.xml',
        'views/fsm_order_view.xml',
    ],
    'installable': True,
}
