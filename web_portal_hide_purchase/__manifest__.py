# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Web Portal Hide Purchase",
    "version": "14.0.1.0.0",
    "author": "Open Source Integrators",
    "summary": """Hides the Purchase Orders section in the customer portal.
    The customer can still open Purchase Orders via a direct link.""",
    "license": "LGPL-3",
    "category": "Purchasing",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "portal",
        "purchase",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/purchase_portal_templates.xml",
    ],
    "installable": True,
    "maintainers": ["patrickrwilson"],
}
