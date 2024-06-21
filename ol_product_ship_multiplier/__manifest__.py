{
    "name": "OnLogic Product Ship Multiplier",
    "summary": "Product Shipping Multiplier.",
    "description": """Product Shipping Multiplier""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Stock",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "purchase_last_price_info",
        "delivery",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/delivery_carrier_multiplier_views.xml",
        "views/product_views.xml",
    ],
}
