# Copyright (C) 2024 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Configurator Sales Blanket Order",
    "version": "17.0.1.0.0",
    "category": "Sale",
    "summary": "Product configuration interface modules for Sales Blanket Order",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/product-configurator",
    "depends": ["sale_blanket_order", "product_configurator"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_blanket_order_view.xml",
    ],
    "installable": True,
    "auto_install": True,
    "development_status": "Alpha",
    "maintainers": ["dreispt"],
}
