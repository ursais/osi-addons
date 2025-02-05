{
    "name": "OnLogic Product Operations Category",
    "summary": """
        Adds ability for Operations to categorize products based on their own needs.
    """,
    "description": """
        Adds functionality similar to the core Odoo `product.category`
        to allow Operations to categorize products based on their own needs.
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Manufacturing",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "product",
    ],
    # always loaded
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/product_operations_category.xml",
        "views/product.xml",
    ],
}
