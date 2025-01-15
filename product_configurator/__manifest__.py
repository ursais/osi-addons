{
    "name": "Product Configurator",
    "version": "17.0.1.0.1",
    "category": "Generic Modules/Base",
    "summary": "Base for product configuration interface modules",
    "author": "Pledra, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-configurator",
    "external_dependencies": {
        "python": [
            "mako",
        ]
    },
    "depends": ["account"],
    "data": [
        "security/configurator_security.xml",
        "security/ir.model.access.csv",
        "views/res_config_settings_view.xml",
        "data/menu_configurable_product.xml",
        "data/product_attribute.xml",
        "data/ir_sequence_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/product_view.xml",
        "views/product_attribute_view.xml",
        "views/product_config_view.xml",
        "wizard/product_configurator_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/product_configurator/static/src/scss/form_widget.scss",
            "/product_configurator/static/src/js/form_widgets.esm.js",
            "/product_configurator/static/src/js/boolean_button_widget.esm.js",
            "/product_configurator/static/src/js/boolean_button_widget.xml",
            "/product_configurator/static/src/js/kanban_widgets.esm.js",
            "/product_configurator/static/src/js/list_widgest.esm.js",
        ]
    },
    "demo": [
        "demo/product_template.xml",
        "demo/product_attribute.xml",
        "demo/product_config_domain.xml",
        "demo/product_config_lines.xml",
        "demo/product_config_step.xml",
        "demo/config_image_ids.xml",
    ],
    "images": ["static/description/cover.png"],
    "post_init_hook": "post_init_hook",
    "development_status": "Beta",
    "maintainers": ["PCatinean"],
    "installable": True,
    "application": True,
    "auto_install": False,
}
