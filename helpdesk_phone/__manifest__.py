# Copyright (C) 2018 - TODAY, Open Source Integrators, Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Helpdesk Phone',
    'summary': 'Add phone class to Helpdesk',
    'version': '11.0.0.0.1',
    'category': 'Helpdesk',
    'author': "Open Source Integrators, Odoo Community Association (OCA), ",
    'website': 'https://github.com/OCA/field-service',
    'depends': [
        'helpdesk',
    ],
    'data': [
        'views/helpdesk_phone.xml'
    ],
    'installable': True,
    'license': 'AGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'wolfhall',
        'max3903',
    ],
}
