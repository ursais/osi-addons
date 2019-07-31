# Copyright (C) 2019 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Fieldservice Account Asset',
    'summary': 'This module aims to link the FSM equipment with its accounting'
               'asset and allow tracking of its depreciation.',
    'version': '12.0.1.0.0',
    'category': 'Field Service',
    'license': 'AGPL-3',
    'author': 'Open Source Integrators',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'fieldservice_stock',
        'agreement_serviceprofile',
        'account_asset',
    ],
    'data': [
        'views/fsm_stage_view.xml',
        'views/fsm_equipment_view.xml',
        'views/fsm_order.xml',
    ],
    'installable': True,
}
