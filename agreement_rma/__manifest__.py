# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Agreement - RMA',
    'summary': 'Link rma orders to an agreement',
    'version': '12.0.1.0.0',
    'category': 'Contract',
    'author': 'Open Source Integrators, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/ursais/osi-addons',
    'depends': [
        'agreement_legal',
        'rma',
    ],
    'data': [
        'views/agreement_view.xml',
        'views/rma_view.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
    'development_status': 'Beta',
    'maintainers': [
        'smangukiya',
        'max3903',
    ],
}
