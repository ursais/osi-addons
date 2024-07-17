{
    "name": "OnLogic Product Lifecycle Management (PLM) Cancel",
    "summary": "OnLogic Product Lifecycle Management (PLM) Cancel.",
    "description": """
        Manage engineering change orders on products cancel.
        """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.0.1.0",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "mrp_plm",
        "product_state",
        "ol_mrp_plm_tier_validation",
    ],
    # always loaded
    "data": [
        "views/mrp_eco_stage.xml",
        "views/mrp_eco_view.xml",
    ],
}
