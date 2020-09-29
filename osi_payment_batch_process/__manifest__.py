# Copyright (C) 2019, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Batch Payments Processing",
    "version": "12.0.1.1.0",
    "author": "Open Source Integrators",
    "summary": """
        OSI Batch Payments Processing for Customers Invoices and
        Supplier Invoices
    """,
    "category": "Extra",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "depends": ["account", "account_check_printing", "account_batch_payment"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/invoice_batch_process_view.xml",
        "views/invoice_view.xml",
    ],
    "external_dependencies": {"python": ["num2words"]},
    "installable": True,
}
