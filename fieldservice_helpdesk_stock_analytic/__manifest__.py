# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Field Service - Helpdesk - Stock - Analytic',
    'summary': 'Track costs of delivered items with analytic accounting',
    'license': 'AGPL-3',
    'version': '12.0.1.0.2',
    'category': 'Helpdesk',
    'author': "Open Source Integrators, ",
    'website': 'https://github.com/OCA/field-service',
    'depends': [
        'fieldservice_helpdesk_stock',
        'stock_request_analytic',
        'fieldservice_account_analytic'
    ],
    'development_status': 'Beta',
    'maintainers': ['max3903'],
}
