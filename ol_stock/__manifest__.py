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
        "ol_templates",
        "ol_stock_loadcsv",
        "stock_inventory",
        "ol_rush_order",
    ],
    # always loaded
    "data": [
        "data/stock_location_data.xml",
        "security/security_group.xml",
        "views/stock_picking_type_views.xml",
        'reports/inventory_label.xml',
        'reports/inventory_sheets.xml',
        'reports/packing_slip_from_so.xml',
        'reports/packing_slip.xml',
        'reports/picking_list_from_so.xml',
        'reports/picking_list.xml',
    ],
}
