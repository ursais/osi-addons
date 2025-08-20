{
    "name": "OnLogic Product Configurator",
    "summary": "OnLogic Product Configurator Customizations.",
    "description": """
        A OnLogic Product Configurator Related Components are added.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Generic Modules/Base",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "product_configurator",
        "product_configurator_mrp",
        "product_configurator_mrp_quantity",
        "product_configurator_sale",
        "sale_product_configurator",
    ],
    # always loaded
    "data": [
        "data/ir_action_server.xml",
        "data/m2x_create_edit_option_data.xml",
        "views/attribute_value_views.xml",
        "views/mrp_bom_views.xml",
        "views/product_attribute_views.xml",
        "views/product_template_attribute_value_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/sale_order_views.xml",
        "wizard/product_configurator_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ol_product_configurator/static/src/js/sale_configurator_patch.js",
        ],
    },
}