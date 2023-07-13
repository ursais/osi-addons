# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI SIMPLE RMA",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Sale",
    "depends": ["sale_management", "stock", "account"],
    "data": [
        "security/security_view.xml",
        "security/ir.model.access.csv",
        "data/customer_simple_rma_seq_view.xml",
        "views/stock_view.xml",
        "views/account_invoice_view.xml",
        "views/customer_simple_rma_view.xml",
        "report/report_productrma.xml",
        "report/product_rma_report.xml",
    ],
    "application": True,
    "installable": True,
}
