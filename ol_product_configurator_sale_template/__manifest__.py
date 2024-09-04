{
    "name": "OnLogic Product Configurator Sale Template",
    "summary": "Product Configurator with Sale Template related customization",
    "description": """Product Configurator with Sale Template related customization.""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_management",
        "sale_mrp",
        "product_configurator",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_template_views.xml",
    ],
}
