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
        # "ol_base",
        "attribute_set",
        "documents_product",
        "product_attribute_set",
    ],
    # always loaded
    "post_init_hook": "load_attribute_csv_data",
    "data": [
        "data/documents_folder.xml",
        "views/product_template_views.xml",
    ],
}
