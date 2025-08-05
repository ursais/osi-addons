{
    "name": "OnLogic Purchase",
    "description": """
        Onlogic Purchasing customizations.
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Purchase",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "purchase",
        "purchase_stock",
        "product",
    ],
    # always loaded
    "data": [
        "views/res_partner_view.xml",
        "views/purchase_order_view.xml",
        "views/product_view.xml",
        "reports/purchase_order_doc.xml",
        "data/purchase_email.xml",
        "views/stock_picking_views.xml",
    ],
}
