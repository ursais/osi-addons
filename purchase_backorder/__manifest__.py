# Copyright (C) 2012 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Purchase Backorder Report',
    'version': '12.0.1.1.0',
    'license': 'AGPL-3',
    'author': 'Open Source Integrators, Odoo Community Association (OCA)',
    'summary': 'Report of Un-Invoiced Goods Received and Backorders',
    'category': 'Purchase',
    'website': 'https://github.com/OCA/purchase-reporting',
    'depends': [
        'account',
        'purchase_stock',
    ],
    'data': [
        'views/po_backorder_view.xml',
        'views/purchase_view.xml',
        'report/po_backorder_report.xml',
        'wizard/po_backorder_wizard_view.xml',
    ],
    'development_status': 'Beta',
    'maintainers': ['smangukiya'],
}
