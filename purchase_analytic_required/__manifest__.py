# Copyright 2024 Open Source Integrators Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Purchase Analytic Required",
    "version": "17.0.1.0.0",
    "author": "Open Source Integrators Inc.",
    "category": "Purchase Management",
    "website": "https://www.opensourceintegrators.com",
    "depends": [
        "purchase_analytic",
        "account_analytic_required",
    ],
    "data": [
        "views/purchase_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "auto_install": True,
}
