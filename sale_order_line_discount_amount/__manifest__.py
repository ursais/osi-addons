# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Discount in Amount",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainer": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "category": "Sale",
    "images": [],
    "depends": [
        "sale",
        "stock_account",
    ],
    "data": [
        'views/sale_view.xml',
        'views/invoice_view.xml',
        'views/report_saleorder.xml',
        'views/report_invoice.xml',
    ],
    "test": [
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
