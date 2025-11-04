# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Product Cost Price",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    Set product cost price with 6 decimals.
    Fix weight computation for configurable product variants.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Purchase",
    "depends": ["product", "purchase", "stock_account"],
    "external_dependencies": {},
    "data": [
        "data/product_decimal.xml",
    ],
    "installable": True,
}
