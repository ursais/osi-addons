# pylint: disable=pointless-statement
{
    "name": "OnLogic API",
    "summary": "API related functionality",
    "version": "1.0",
    "depends": ["ol_base", "ol_graphql"],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "description": """API related functionality.""",
    "data": [
        "data/api_clients.xml",
        "data/external_system.xml",
        "security/ir.model.access.csv",
        "views/api.xml",
        "views/graphql.xml",
        "views/external_system.xml",
    ],
}
