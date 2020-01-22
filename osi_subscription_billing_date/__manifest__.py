# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sale Subscription Billing Date",
    "summary": "Customer subscriptions billed on selected day of the month",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": [
        'osi_subscription_prorate',
        # ... used for the prorata caclulations
        # needed when a billing day is changed
    ],
    "data": [
        "views/res_partner.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["osi-scampbell"],
}
