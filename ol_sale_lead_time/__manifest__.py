{
    "name": "OnLogic Sale Lead Time Compute",
    "summary": "Compute lead time on sale order line based on availability.",
    "description": """Compute lead time on sale order line based on availability.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_management",
        "mrp",
        "product_configurator_sale",
    ],
    # always loaded
    "data": [
        "views/sale_order_view.xml",
        "views/res_config_settings_views.xml",
    ],
}
