{
    "name": "Onlogic Sale Stock Tags",
    "summary": """
        Extends the functionality of sale stock tags.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Stock",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_stock",
    ],
    # always loaded
    "data": [
        "views/stock_picking_view.xml",
    ],
    "application": False,
    "installable": True,
}
