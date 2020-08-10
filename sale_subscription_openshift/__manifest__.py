# Copyright (C) 2020 Open Source Integrators
# Copyright (C) 2020 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Sale Subscription Openshift",
    "summary": """Sale Subscription Openshift""",
    "version": "13.0.1.0.0",
    "license": "LGPL-3",
    "author": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Sales",
    "depends": ["connector_openshift", "sale_subscription_suspend"],
    "data": [
        "views/product_template_views.xml",
        "views/sale_subscription_views.xml",
        "data/mail_template_data.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["max3903"],
}
