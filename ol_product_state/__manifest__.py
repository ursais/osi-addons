{
    "name": "Onlogic Product State",
    "summary": """
        Extends the functionality of product state change process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Product",
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        "product_state",
    ],
    # always loaded
    "data": [
        "security/product_state_group.xml",
        "views/product_template_view.xml",
    ],
    "application": False,
    "installable": True,
}
