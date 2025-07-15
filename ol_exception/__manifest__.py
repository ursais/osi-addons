{
    "name": "OnLogic Exception handling",
    "summary": "Add group for python access to exception rules.",
    "description": """
        Adding the Group for Adding a Python code in Base Exception.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "base_exception",
        "sale_exception",
        "product_state",
        "purchase_exception",
        "stock_exception",
        "mrp_exception",
        "mrp_batch",
    ],
    # always loaded
    "data": [
        "security/base_exception_security.xml",
        "security/ir.model.access.csv",
        "views/exception_config.xml",
        "views/exception_rule_view.xml",
        "views/product_state_views.xml",
        "views/purchase_order_view.xml",
        "views/sale_order_view.xml",
        "views/stock_view.xml",
        "data/exception_config_data.xml",
        "data/exception_data.xml",
    ],
}
