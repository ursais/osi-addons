# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI Display Incoming Product",
    "summary": "Displays Incoming products on product",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "Stock",
    "depends": ["stock"],
    "data": [
        "views/product_template_view.xml",
        "views/product_views.xml",
        "views/stock_move_views.xml",
    ],
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["patrickrwilson"],
}
