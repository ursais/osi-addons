{
    "name": "OnLogic Sale customization",
    "summary": "Sale modules related customization",
    "description": """Sale modules related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_management",
        "product_state",
    ],
    # always loaded
    "data": [
        "views/sale_order_view.xml",
    ],
}
