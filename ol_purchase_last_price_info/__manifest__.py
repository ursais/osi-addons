{
    "name": "OnLogic Purchase Product Last Price Info",
    "description": """
        Reviews pricing when Last PO Cost changes for components
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Purchase",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "purchase",
        "purchase_last_price_info",
    ],
    "demo": [],
    # always loaded
    "data": [],
}
