{
    "name": "OnLogic Product Classification",
    "summary": "Adds Product Classification functionality",
    "description": """Adds Product Classification functionality""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "product",
    ],
    # always loaded
    "data": [
        "data/classification.xml",
        "security/ir.model.access.csv",
        "views/classification.xml",
        "views/mrp.xml",
        "views/product.xml",
        "views/product_attribute_view.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/classification.xml",
        "demo/product_attribute.xml",
    ],
}
