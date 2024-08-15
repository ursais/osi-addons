{
    "name": "OnLogic Product Lifecycle Management (PLM)",
    "summary": "OnLogic Product Lifecycle Management (PLM) Customization.",
    "description": """
        Manage engineering change orders on products, bills of material.
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
        "mrp_plm",
        "product_state",
        "ol_product_state",
        "ol_mrp_plm_tier_validation",
    ],
    # always loaded
    "data": [
        "security/bom_restiction_group.xml",
        "views/mrp_eco_stage.xml",
        "data/mrp_eco_tags.xml",
        "data/plm_types.xml",
        "data/plm_stages.xml",
        "data/tier_definition.xml",
    ],
}
