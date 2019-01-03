# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock Production Lot Warranty",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "summary": "Add expiration date to stock produciton lot",
    "category": "Stock",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "stock",
        "fieldservice",
        "fieldservice_stock"
    ],
    "data": [
        'views/stock_production_lot.xml',
    ],
    "installable": True,
}
