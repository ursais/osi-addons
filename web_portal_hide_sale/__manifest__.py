# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Web Portal Hide Sale",
    "version": "14.0.1.0.0",
    "author": "Open Source Integrators",
    "summary": """Hides the Sales/Quotes section in the customer portal.
    The customer can still open sales orders/quotations via a direct link.""",
    "license": "LGPL-3",
    "category": "Sales",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "portal",
        "sale",
    ],
    "data": [
        "views/res_partner_views.xml",
        "views/sale_portal_templates.xml",
    ],
    "installable": True,
    "maintainers": ["patrickrwilson"],
}
