{
    "name": "OnLogic Scrap Reason Code",
    "summary": "OnLogic Scrap Reason Code.",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Warehouse Management",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "scrap_reason_code",
    ],
    # always loaded
    "data": [
        "security/ir_rule.xml",
        "views/reason_code_view.xml",
        "views/stock_scrap_views.xml",
        "views/stock_move_views.xml",
    ],
}
