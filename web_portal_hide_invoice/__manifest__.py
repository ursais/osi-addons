# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Web Portal Hide Invoice/Bills",
    "version": "14.0.1.0.0",
    "author": "Open Source Integrators",
    "summary": """Hides the Invoices/Bills section in the customer portal.
    The customer can still open Invoices/Bills via a direct link.""",
    "license": "LGPL-3",
    "category": "Accounting",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "portal",
        "account",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/account_portal_templates.xml",
    ],
    "installable": True,
    "maintainers": ["patrickrwilson"],
}
