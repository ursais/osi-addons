{
    "name": "Onlogic Product Pricing Review",
    "summary": "Product Price Tracking and Review",
    "description": """Product Price Change Tracking and Review.""",
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Stock",
    "version": "17.0.0.1.0",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "ol_product_ship_multiplier",
        "ol_product_tooling_cost",
        "ol_product_tariff",
        "ol_purchase_last_price_info",
        "stock",
        "stock_account",
    ],
    # Data Loaded.
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/pa_sequence.xml",
        "views/product_category_views.xml",
        "views/product_price_review_views.xml",
        "views/product_product_views.xml",
        "views/product_template_views.xml",
    ],
}
