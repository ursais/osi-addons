{
    "name": "OnLogic Create Product Wizard",
    "summary": "Adds wizard to create products from other products.",
    "description": """Adds wizard to create products from other products.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_product_configurator",
        "ol_pim",
        "ol_sale",
        "ol_product",
        "sale_management",
        "mrp_plm",
    ],
    # always loaded
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "views/menu_items.xml",
        "wizard/product_create_wizard.xml",
    ],
}
