{
    "name": "Onlogic Partner Credit Limit",
    "summary": """
        Extends the functionality of Partner Credit Limit process.
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
        "sale_exception",
        "mrp_exception",
        "stock_exception",
        "ol_sale_mrp_tags",
        "account",
        "ol_exception",
    ],
    # always loaded
    "data": [
        "security/credit_limit_group.xml",
        "data/function.xml",
        "data/credit_limit_data.xml",
        "data/exception_config_data.xml",
        "views/res_partner.xml",
        "views/sale_order_view.xml",
        "views/stock_picking_view.xml",
        "views/mrp_production_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'ol_credit_limit/static/src/**/*',
        ],
    },
    # only loaded in demo mode
    "demo": [],
    "application": False,
    "installable": True,
}
