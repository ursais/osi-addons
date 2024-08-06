{
    "name": "Onlogic Product PIM",
    "summary": "Onlogic Product PIM",
    "description": """
    Onlogic Product PIM
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "product_attribute_set",
    ],
    # always loaded
    "data": [
        "data/attribute.set.csv",
        "data/attribute.group.csv",
        "data/attribute.attribute.csv",
        "data/attribute.option.csv",
        "views/product_template_views.xml",
    ],
}
