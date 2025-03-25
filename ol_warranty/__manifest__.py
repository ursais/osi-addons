{
    "name": "Onlogic Warrnty",
    "summary": """
        Add warranty expiration date to serial numbers
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Product",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "stock",
        "repair",
    ],
    # always loaded
    "data": [
        "views/stock_lot_views.xml",
        "views/repair_order_views.xml",
        "views/product_template_views.xml",
    ],
    # only loaded in demo mode
    "demo": [],
    "application": False,
    "installable": True,
}
