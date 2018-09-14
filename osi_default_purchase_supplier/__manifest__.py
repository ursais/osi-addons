# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Default Purchase Supplier",
    "summary": "Restrict generic product to confirm order, set default "
               "supplier as a generic supplier in PO",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "category": "Purchase",
    "website": "http://www.opensourceintegrators.com",
    "depends": ["purchase", "sale"],
    "data": [
        "views/res_partner_view.xml",
        "views/res_partner_data.xml",
        "views/purchase_view.xml",
        "views/product_view.xml",
        "views/product_template_data.xml",
    ],
    "installable": True,
}
