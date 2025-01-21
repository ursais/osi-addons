# Copyright (C) 2024, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "OSI NACHA 80byte",
    "countries": ["us"],
    "summary": """Export payments as NACHA 80byte""",
    "category": "Accounting",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "l10n_us_payment_nacha",
    ],
    "data": [
        "data/ir_sequence.xml",
        "views/account_journal_views.xml",
    ],
    "installable": True,
}
