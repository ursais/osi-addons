{
    "name": "Onlogic Tooling Costs on Products",
    "summary": "Store and sync tooling_cost & defrayment_cost fields on products.",
    "description": """
    Some products have tooling costs applied to them. We need to be able to sync those values
    and use them when creating quote workups.
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "product",
    ],
    # always loaded
    "data": ["views/product.xml"],
}
