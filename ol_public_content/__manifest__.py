{
    "name": "OnLogic Public Content",
    "summary": "Adds support for public content",
    "description": """Adds support for public content""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
    ],
    # always loaded
    "data": [
        "views/document_views.xml",
    ],
}
