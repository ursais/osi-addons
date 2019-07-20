# Copyright (C) 2019 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Sale Subscription Brand",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/OCA/sale-workflow",
    "author": [
        "Open Source Integrators",
        "Odoo Community Association (OCA)",
    ],
    "license": "AGPL-3",
    "depends": [ 
        'sale_subscription',
        'partner_brand',
        'sale_brand'
    ],
    "data": [
        "views/sale_subscription_views.xml",
    ],
    "installable": True,
}