{
    "name": "OnLogic Stock customization",
    "summary": "Stock modules related customization",
    "description": """Stock modules related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "stock",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "stock",
        "delivery_stock_picking_batch",
    ],
    'assets': {
        'web.assets_backend': [
            'ol_stock/static/src/js/receipt_non_editable.js',
        ],
    },
    # always loaded
    "data": [
        "data/stock_location_data.xml",
    ],
}
