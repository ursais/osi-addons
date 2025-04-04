{
    "name": "OnLogic Product Customization",
    "summary": "Adds OnLogic Product Customization",
    "description": """Adds OnLogic Product Customization""",
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
        "reports/product_labels.xml",
    ],
}
