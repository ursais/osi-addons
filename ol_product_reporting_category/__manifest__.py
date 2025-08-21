{
    "name": "Onlogic Product Reporting Category",
    "summary": """
        Add the functionality of product reporting categories.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Product",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "stock",
    ],
    # always loaded
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/product_reporting_category.xml",
        "views/product_reporting_line.xml",
        "views/product_reporting_series.xml",
        "views/product_reporting_system.xml",
        "views/product_template_view.xml",
    ],
    # only loaded in demo mode
    "demo": [],
    "application": False,
    "installable": True,
    # Run hook after install to set products report category
    "post_init_hook": "post_init_hook",
}
