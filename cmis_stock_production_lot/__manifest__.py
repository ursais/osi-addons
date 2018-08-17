# -*- coding: utf-8 -*-
# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    "name": "CMIS Stock Production Lot",
    "summary": "Upload CMIS documents on the Lot/SN Number",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "category": "Inventory",
    "maintainer": ["max3903"],
    "development_status": "Beta",
    "website": "https://github.com/OCA/connector-cmis",
    "depends": [
        "stock",
        "cmis_web",
    ],
    "data": [
        "views/stock_production_lot.xml",
    ],
    "application": False,
}
