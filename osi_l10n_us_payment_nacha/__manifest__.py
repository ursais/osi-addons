# Copyright (C) 2022, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI NACHA Payments",
    "license": "AGPL-3",
    "icon": "/l10n_us/static/description/icon.png",
    "summary": """Extends NACHA payment files""",
    "category": "Accounting/Accounting",
    "version": "16.0.1.0.0",
    "website": "https://github.com/ursais/osi-addons",
    "author": "Open Source Integrators",
    "depends": ["l10n_us_payment_nacha"],
    "data": [
        "data/l10n_us_payment_nacha_ccd.xml",
    ],
    "installable": True,
    "maintainers": "[opensourceintegrators]",
}
