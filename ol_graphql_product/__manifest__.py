# pylint: disable=pointless-statement
{
    "name": "OnLogic GraphQL - Product",
    "summary": "Product specific GraphQL functionality",
    "version": "1.0",
    "license": "AGPL-3",
    "depends": [
        "ol_base",
        "ol_graphql",
        "ol_pim",
        "ol_product_classification",
        "ol_product_pricing_review",
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
