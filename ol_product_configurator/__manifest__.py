{
    "name": "OnLogic Product Configurator",
    "summary": "OnLogic Product Configurator Customization.",
    "description": """
        A OnLogic Product Configurator Related Components are added.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Generic Modules/Base",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": ["ol_base", "product_configurator"],
    # always loaded
    "data": [
        "security/ir_rule.xml",
        "views/attribute_value_views.xml",
        "views/product_template_attribute_value_views.xml",
    ],
}
