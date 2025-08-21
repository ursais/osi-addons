{
    "name": "OnLogic Sale Archive Check",
    "summary": "Add checks for archived product/boms.",
    "description": """Add checks for archived product/boms.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_product_configurator",
        "ol_exception",
        "ol_sale_substate",
        "queue_job",
        "sale_order_line_menu",
        "sale",
    ],
    # always loaded
    "data": [
        "views/sale_order_view.xml",
        "data/sale_exception.xml",
    ],
}
