# Copyright (C) 2019 Amplex
# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': "Sale Subscription Financial Risk",
    'summary': """
        Extends Financial risk to support service suspension activities.""",
    'author': "Open Source Integrators, Amplex Internet",
    'website': "https://github.com/ursais/osi-addons",
    'category': 'Agreement',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'depends': [
        'account_financial_risk',
        'sale_subscription',
        'sale_subscription_suspend'
    ],
    'data': [
        'data/base_automation.xml',
        'data/ir_cron.xml',
        'views/res_partner_views.xml'
    ],
    'development_status': 'Beta',
    'maintainers': [
        'kvedder-amplex',
        'barnarj-amplex',
    ],
    'installable': True,
}
