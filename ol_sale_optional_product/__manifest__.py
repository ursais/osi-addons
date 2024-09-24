{
    "name": "OnLogic Sale Add Optional Products",
    "summary": "Create Optional Products from Sale Lines.",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_management",
        "product_state",
    ],
    # always loaded
    "data": [
        "report/sale_report_templates.xml",
        "views/sale_order_view.xml",
    ],
}
