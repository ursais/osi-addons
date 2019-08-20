# Copyright (C) 2019 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Agreement - Sales Subscription Suspension',
    'summary': 'Changes the state of service profiles based upon a '
               'subscription being suspended or activated / re-activated.',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'Open Source Integrators',
    'category': 'Agreement',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'agreement_sale_subscription',
        'agreement_serviceprofile',
        'sale_subscription_suspend'
        ],
    'installable': True,
}
