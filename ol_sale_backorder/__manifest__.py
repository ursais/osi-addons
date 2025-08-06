{
    "name": "OnLogic Sale Backorder",
    "summary": "Block/cap quantities when No Backorders on product or BoM components.",
    "description": """Block/cap quantities when No Backorders on product or BoM components.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_sale",
        "stock",
        "mrp",
        "product_configurator_sale_mrp",
    ],
    # always loaded
    "data": [],
}
