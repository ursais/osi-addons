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
    # any module necessary for this one to work correctly
    "depends": [
        "sale_stock",
    ],
    # always loaded
    "data": [
        "views/stock_picking_view.xml",
    ],
    "application": False,
    "installable": True,
}
