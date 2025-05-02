{
    "name": "OnLogic Stock Constrained availability",
    "summary": "Adds OnLogic Stock Constrained availability",
    "description": """Adds OnLogic Stock Constrained availability""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": ["ol_base", "mrp_batch", "mrp"],
    # always loaded
    "data": ["views/product_template_views.xml", "views/sale_order_views.xml",],
}
