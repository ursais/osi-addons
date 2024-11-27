# Copyright 2021 Open Source Integrators
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Ol Rush Order",
    "summary": "create rush order",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/partner-contact",
    "category": "Sales/CRM",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["product_configurator","sale_management","mrp", "ol_base"],
    "data": [
        "views/product_template_view.xml",
        "views/mrp_production_view.xml",
        "views/sale_order_view.xml",
        "views/stock_picking.xml",
    ],
    "installable": True,
}