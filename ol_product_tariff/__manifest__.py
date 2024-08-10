# pylint: disable=pointless-statement
{
    "name": "OnLogic Tariffs on Products",
    "summary": "Store and sync tariff field on products.",
    "description": """
        Some products have tariffs applied to them. We need to be able to sync those values and
        use them when creating quote workups.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "product",
        "sale",
        "ol_base",
    ],
    # always loaded
    "data": [
        "views/product_views.xml",
        "views/tariff_views.xml",
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
    ],
    # only loaded in demo mode
    "demo": [
        "demo/tariff_code.xml",
    ],
}
