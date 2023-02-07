# Copyright (C) 2021, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Product BOM Cost Rollup",
    "version": "14.0.1.0.1",
    "author": "Open Source Integrators",
    "summary": """Update BOM costs by rolling up. Adds scheduled job for
                  unattended rollups.""",
    "license": "LGPL-3",
    "category": "Product",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "mrp",
        "mrp_account",
        "stock_account",
        "osi_prod_avgpurchaseprice",
    ],
    "data": [
        "views/product_views.xml",
        "views/mrp_bom.xml",
        "views/res_config_settings.xml",
        "data/cost_rollup_scheduler.xml",
    ],
    "installable": True,
    "auto_install": False,
}
