# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Product Cost Price",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "summary": """
    Set product cost price with 6 decimals.
    """,
    "author": "Open Source Integrators",
    "maintainers": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Purchase",
    "depends": ["product", "purchase", "stock_account"],
    "data": [
        "data/product_decimal.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
