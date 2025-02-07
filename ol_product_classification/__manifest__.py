# pylint: disable=pointless-statement
{
    "name": "OnLogic Product Classification",
    "summary": "Adds Product Classification functionality",
    "version": "17.0.0.1.0",
    "depends": [
        "ol_base",
        "product",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales",
    "description": """Adds Product Classification functionality""",
    "data": [
        "data/classification.xml",
        "security/ir.model.access.csv",
        "views/classification.xml",
        "views/mrp.xml",
        "views/product.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/classification.xml",
        "demo/product_attribute.xml",
    ],
}
