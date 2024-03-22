# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Configurator - Restriction Policy",
    "version": "17.0.1.0.0",
    "category": "Generic Modules",
    "summary": "Adds a Restriction Policy for processing restrictions.",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-configurator",
    "depends": ["product_configurator"],
    "data": [
        "views/res_config_settings_view.xml",
        "views/product_view.xml",
    ],
    "development_status": "Beta",
    "installable": True,
    "application": False,
}
