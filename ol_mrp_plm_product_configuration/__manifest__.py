{
    "name": "OnLogic PLM Product Configuration Change Staging",
    "summary": "OnLogic PLM Product Configuration Change Staging.",
    "description": """
        Adds the ability to make changes to attributes/values then apply via PLM.
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
        "ol_mrp_plm",
        "ol_mrp_plm_tier_validation",
        "ol_mrp_bom_rebuild",
        "mrp_plm",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_eco_type_views.xml",
        "views/mrp_eco_views.xml",
    ],
}
