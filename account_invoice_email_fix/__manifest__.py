# Copyright (C) 2024 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Account Invoice Email Fix",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "license": "LGPL-3",
    "summary": "Fix invoice email subject to properly display sale order or invoice name",
    "description": """
        Fixes the invoice email template subject line to properly display:
        - Sale order name if a sale order exists (first sale order found)
        - Invoice name if no sale order exists
        Resolves issue where template syntax was showing raw template code instead of values.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["opensourceintegrators"],
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "account",
        "sale",
    ],
    "data": [
        "data/mail_template_data.xml",
    ],
    "installable": True,
}
