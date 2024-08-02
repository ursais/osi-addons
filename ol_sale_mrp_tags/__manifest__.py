{
    "name": "Onlogic Sale MRP Tags",
    "summary": """
        Extends the functionality of sale MRP tags.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Stock",
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_mrp",
        "sale_stock",
    ],
    # always loaded
    "data": [
        "views/mrp_production_view.xml",
    ],
    "application": False,
    "installable": True,
}
