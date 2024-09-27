{
    "name": "Onlogic Product State",
    "summary": """
        Extends the functionality of product state change process.
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
        "product_state",
        "sale_product_approval",
        "sale_product_approval_purchase",
        "sale_product_approval_mrp",
        "sale_product_approval_stock",
    ],
    # always loaded
    "data": [
        "security/product_state_group.xml",
        "views/product_template_view.xml",
        "views/product_category_views.xml",
        "data/product_state_data.xml",
        "data/product_category_data.xml",
    ],
    # only loaded in demo mode
    "demo": [],
    "application": False,
    "installable": True,
}
