# Copyright (C) 2017 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Vendor Product Return",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Purchases",
    "depends": ["purchase", "stock", "account"],
    "data": [
        "security/security_view.xml",
        "security/ir.model.access.csv",
        "data/vendor_product_return_seq_view.xml",
        "views/stock_view.xml",
        "views/account_invoice_view.xml",
        "views/return_reason_view.xml",
        "views/vendor_product_return_view.xml",
        "report/product_return_report.xml",
        "report/report_productreturn.xml",
    ],
    "application": True,
    "installable": True,
}
