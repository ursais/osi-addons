{
    "name": "DO NOT USE: REPLACED WITH OCA sale_blanket_order_tier_validation",
    "summary": """
        Extends the functionality of your Sale Blanket Orders
        to support a tier validation process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "sale_blanket_order",
        "base_tier_validation",
    ],
    # always loaded
    "data": [
        "views/sale_blanket_order_views.xml",
    ],
    "application": False,
    "installable": True,
}
