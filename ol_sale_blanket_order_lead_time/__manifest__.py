{
    "name": "OnLogic Sale Blanket Order Lead Time Compute",
    "summary": "Compute lead time on sale blanket order line based on availability.",
    "description": """
    Compute lead time on sale blanket order line based on availability.
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_sale_blanket_order",
        "mrp",
        "product_configurator_sale_blanket_order",
        "product_configurator_sale_blanket_order_mrp",
    ],
    # always loaded
    "data": [
        "views/sale_blanket_order_view.xml",
    ],
}
