# pylint: disable=pointless-statement
{
    "name": "Blind Drop Shipping Updates",
    "onlogic": True,
    "summary": """Allow blind drop shipping""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    # Categories can be used to filter modules in modules listing
    "category": "Inventory",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_stock",
    ],
    # always loaded
    "data": [
        "views/stock_picking.xml",
        "views/res_config_settings.xml",
    ],
    # only loaded in demonstration mode
    "demo": ["demo/blind_drop_ship.xml"],
}
