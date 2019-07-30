{
    'name': "sale_subscription_financial_risk",
    'summary': """
        Extends Financial risk to support service suspension activities.""",
    'author': "Open Source Integrators / Amplex Internet",
    'website': "http://www.amplex.net",
    'category': 'Agreement',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account_financial_risk'
    ],
    'data': [
        'views/sale_subscription_financial_risk_views.xml',
    ],
    'development_status': 'Beta',
    'maintainers': [
        'kvedder-amplex',
        'barnarj-amplex'
    ],
    'installable': True,
}
