{
    "name": "Onlogic Product Currency",
    "summary": """
        Changes the product template currency_id compute method to act the same
        as cost_currency_id compute
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
        "product",
    ],
    # always loaded
    "data": [],
    "installable": True,
}
