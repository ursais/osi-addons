{
    "name": "Onlogic PIM",
    "summary": "Onlogic PIM",
    "description": """
    Onlogic PIM
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Products",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
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
