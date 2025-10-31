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
    "version": "17.0.0.1.1",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "attribute_set",
        "documents_product",
        "product_attribute_set",
    ],
    # load on initial install
    "post_init_hook": "load_attribute_csv_data",
    # always loaded
    "data": [
        "data/documents_folder.xml",
        "data/ir_actions_server.xml",
        "views/attribute_attribute_views.xml",
        "views/attribute_group_views.xml",
        "views/attribute_option_views.xml",
        "views/attribute_set_views.xml",
        "views/product_template_views.xml",
    ],
}
