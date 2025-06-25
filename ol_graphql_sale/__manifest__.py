# pylint: disable=pointless-statement
{
    "name": "OnLogic GraphQL - Sale",
    "summary": "Sale specific GraphQL functionality",
    "version": "1.0",
    "license": "AGPL-3",
    "depends": [
        "ol_base",
        "product_configurator_sale",
        "ol_graphql",
        "ol_exception",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "graphql": True,
    "category": "Integrations",
    "description": """Sale specific GraphQL functionality""",
    "data": [
        "data/sale_exception.xml",
        "views/sale_order.xml",
    ],
}
