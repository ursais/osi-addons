{
    "name": "OnLogic Sale Backorder Workflow Emails",
    "summary": "This module handles the Sale Backorder Workflows Emails",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_exception",
    ],
    # always loaded
    "data": [
        "data/backorder_email.xml",
        "data/sale_exception.xml",
        "views/product_template_views.xml",
        "views/sale_order_views.xml",
    ],
}
