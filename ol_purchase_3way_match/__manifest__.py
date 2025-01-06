{
    "name": "OnLogic Purchase 3 way match",
    "summary": """
        Purchase 3 way match adding visiblity if bill line price doesn't match PO line.
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
    ],
    # always loaded
    "data": [
        "views/account_move_views.xml",
    ],
}
