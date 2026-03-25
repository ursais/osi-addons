# Copyright (C) 2025 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Authorize.net Fee Product",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment",
    "license": "LGPL-3",
    "summary": "Configure a fee product on Authorize.net to track processing"
    " fees and keep accounting balanced",
    "author": "Open Source Integrators",
    "maintainers": ["opensourceintegrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "account_payment",
        "payment_authorize",
    ],
    "data": [
        "views/payment_provider_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
