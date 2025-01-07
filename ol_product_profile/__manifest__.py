{
    "name": "Onlogic Product Profile",
    "summary": """
        Extending the product profile functionality includes information on extending it to other fields.
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
        "product_profile",
        "stock",
    ],
    # always loaded
    "data": [
        "views/product_profile_views.xml",
    ],
    "installable": True,
}
