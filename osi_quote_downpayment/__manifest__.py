# Copyright (C) 2024, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Quote Downpayment",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "category": "Sales",
    "maintainer": "Open Source Integrators",
    "summary": "Allow downpayments on Quote",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "sale",
        "account",
    ],
    "data": [
        "views/sale_order_views.xml",
        "wizards/sale_make_invoice_advance_views.xml",
    ],
    "installable": True,
    "maintainers": ["bodedra"],
}
