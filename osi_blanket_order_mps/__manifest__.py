# Copyright (C) 2022 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Blanket Order MPS",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "maintainers": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Purchase",
    "depends": ["sale_blanket_order", "mrp_mps"],
    "data": [
        "wizard/create_sale_orders.xml",
        "views/mrp_mps_views.xml",
        "views/sale_blanket_order_views.xml",
        "views/sale_blanket_order_line_views.xml",
        "views/assets.xml",
    ],
    "auto_install": False,
    "application": False,
    "installable": True,
}
