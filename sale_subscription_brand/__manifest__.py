# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Sale Subscription Brand",
    "summary": "Brand your subscription invoices",
    "version": "12.0.1.0.0",
    "category": "Sales Management",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "license": "LGPL-3",
    "depends": [
        'sale_subscription',
        'sale_brand',
    ],
    "data": [
        "views/sale_subscription_views.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["osi-scampbell"],
}
