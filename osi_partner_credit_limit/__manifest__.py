# Copyright (C) 2019 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Partner Credit Limit",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "category": "Sales",
    "maintainer": "Open Source Integrators",
    "summary": "Enforce Partner Credit Limit",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "sale",
        "sale_stock",
        "stock",
    ],
    "data": [
        "security/osi_partner_credit_limit.xml",
        "data/picking_data.xml",
        "views/res_partner.xml",
        "views/sale.xml",
        "views/stock.xml",
    ],
    "installable": True,
    "maintainers": ["bodedra"],
}
