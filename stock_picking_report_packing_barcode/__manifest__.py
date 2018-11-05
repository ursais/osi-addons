# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Packing Barcode on Picking Report",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "summary": "Print the Packing Barcode on the Picking Report",
    "category": "Stock",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "stock",
        "sale",
    ],
    "data": [
        'report/report_stockpicking_operations.xml',
    ],
    "installable": True,
}
