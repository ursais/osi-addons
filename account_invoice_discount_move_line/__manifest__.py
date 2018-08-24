# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Discount Account Move Line",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "maintainer": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "category": "Sale",
    "images": [],
    "depends": [
        "sale_order_line_discount_amount",
    ],
    "data": [
        'views/company_view.xml',
    ],
    "test": [
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
