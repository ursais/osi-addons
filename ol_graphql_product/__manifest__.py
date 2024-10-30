# pylint: disable=pointless-statement
{
    "name": "OnLogic GraphQL - Product",
    "summary": "Product specific GraphQL functionality",
    "version": "1.0",
    "depends": [
        "ol_base",
        "ol_graphql",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "graphql": True,
    "category": "Integrations",
    "description": """Product specific GraphQL functionality""",
    "data": [
        "security/ir.model.access.csv",
        "views/product_template.xml",
    ],
    "demo": [
        "demo/products.xml",
    ],
}
