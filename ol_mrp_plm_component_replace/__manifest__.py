{
    "name": "OnLogic PLM Component Replacement",
    "summary": "OnLogic PLM Customization to ease component replacements.",
    "description": """
        Adds an easy way to replace components in multiple BoM's.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_product_configurator",
        "mrp_plm",
    ],
    # always loaded
    "data": [
        "data/mrp_eco_tags.xml",
        "data/plm_types.xml",
        "data/plm_stages.xml",
        "views/mrp_eco_type_views.xml",
        "views/mrp_eco_views.xml",
    ],
}
