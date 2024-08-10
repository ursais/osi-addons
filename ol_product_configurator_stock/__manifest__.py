{
    "name": "OnLogic Product Configurator Stock Customization",
    "summary": "Display Information on the Product Configuration wizard.",
    "description": """
        Additional Information such as On Hand Quantity,
        Available to Use Quantity, and Product State.
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
        "ol_product_state",
        "product_configurator",
    ],
}
