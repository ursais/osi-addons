{
    "name": "OnLogic Sale Template",
    "summary": "Sale Template related customization",
    "description": """Sale Template related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_management"
    ],
    # always loaded
    "data": [
        "views/sale_order_template_views.xml",
    ],
}
