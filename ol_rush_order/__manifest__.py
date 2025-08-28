{
    "name": "Onlogic Rush Orders",
    "description": """
        Create rush orders
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales/CRM",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_product_configurator",
        "product_configurator",
        "sale_management",
        "mrp",
        "mrp_batch",
    ],
    # always loaded
    "data": [
        "data/mrp_production_batch_tag_data.xml",
        "views/product_template_view.xml",
        "views/mrp_production_batch_view.xml",
        "views/mrp_production_view.xml",
        "views/sale_order_view.xml",
        "views/stock_picking.xml",
        "views/product_product_view.xml",
    ],
    "installable": True,
}
