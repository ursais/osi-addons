{
    "name": "OnLogic Sale Substate Customization",
    "summary": "Sale Substate related customization",
    "description": """Sale Substate related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_sale",
        "sale_mrp",
        "sale_stock",
        "sale_substate",
    ],
    # always loaded
    "data": [
        "data/sale_substate_data.xml",
    ],
}
