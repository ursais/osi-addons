# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sale Subscription Consolidated Subscription Invoices",
    "summary": "Consolidated subscription bill dates",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": [
        'account_invoice_consolidated',
        'sale_subscription',
        'osi_subscription_billing_date',
        # ... bacause of the Customer billing day,
        # used to know when to perform the Customer's invoice consolidation
    ],
    "data": [
        "data/consolidated_invoice_data.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["osi-scampbell"],
}
