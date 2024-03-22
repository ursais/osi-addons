# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Configurator Manufacturing",
    "version": "17.0.1.0.0",
    "category": "Manufacturing",
    "summary": "BOM Support for configurable products",
    "author": "Pledra, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-configurator",
    "depends": ["mrp_account", "product_configurator"],
    "data": [
        "data/menu_product.xml",
        "views/mrp_view.xml",
        "security/configurator_security.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "/product_configurator_mrp/static/src/js/list_controller.js",
            "/product_configurator_mrp/static/src/js/kanban_controller.js",
            "/product_configurator_mrp/static/src/js/form_controller.js",
            "/product_configurator_mrp/static/src/scss/mrp_config.scss",
            "/product_configurator_mrp/static/src/xml/mrp_production_views.xml",
        ],
    },
    "demo": ["demo/product_template.xml"],
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["PCatinean"],
}
