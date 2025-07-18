{
    "name": "Onlogic Sale Order Inspections",
    "description": """
        Ability to apply manual order inspections to sale order
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales/CRM",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_exception",
        "stock_exception",
        "mrp_exception",
    ],
    # always loaded
    "data": [
        "data/inspection_data.xml",
        "data/exception_data.xml",
        "security/ir.model.access.csv",
        "views/sale_order_inspection_view.xml",
        "views/sale_order_view.xml",
        "wizard/sale_order_inspection_wiz_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "ol_sale_order_inspection/static/src/css/main.css",
        ],
    },
    "installable": True,
}
