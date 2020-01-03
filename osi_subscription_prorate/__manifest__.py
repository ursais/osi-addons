# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sale Subscription Prorating",
    "summary": "Consolidated subscription bill dates",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": [
        'sale_subscription',
        'sale_subscription_invoice_variable',
        # ... because the of the recurring_last_date field,
        # needed to determine the period to query variable
        # amounts from the Analytic Accounts
    ],
    "data": [
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["osi-scampbell"],
}
