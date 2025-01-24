{
    "name": "OnLogic Sale customization",
    "summary": "Sale modules related customization",
    "description": """Sale modules related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_product_configurator",
        "sale_management",
        "product_state",
        "sale_subscription",
        "stock",
        "product_configurator_sale_mrp",
    ],
    # always loaded
    "data": [
        "data/crm_tag_data.xml",
        "data/product_state_data.xml",
        "views/product_attribute_views.xml",
        "views/product_template_attribute_line_views.xml",
        "views/sale_order_view.xml",
        "views/res_partner_view.xml",
        "views/sale_subscription_views.xml",
        "views/stock_picking_view.xml",
        "views/mrp_production_view.xml",
    ],
}
