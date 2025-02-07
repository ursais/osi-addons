{
    "name": "OnLogic Manufacturing Traveler",
    "summary": "Functionality to define and generate travelers",
    "description": """
        Adds the ability to print manufacturing travelers from many places.
        *** THIS MODULE WILL BE DEPRECATED SOON ***
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Manufacturing",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "base",
        "ol_base",
        "ol_product_classification",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "data/assembly.xml",
        "views/assembly.xml",
        "views/product.xml",
        "views/mrp.xml",
        "views/classification.xml",
        "views/menu.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        "demo/stage.xml",
        "demo/classification.xml",
        "demo/check.xml",
    ],
}
