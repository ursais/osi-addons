# pylint: disable=pointless-statement
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
    # any module necessary for this one to work correctly
    "depends": ["mrp_plm", "product_state"],
    # always loaded
    "data": ["views/mrp_eco_stage.xml"],
}
