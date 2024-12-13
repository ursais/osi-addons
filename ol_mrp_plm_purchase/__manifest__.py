{
    "name": "OnLogic Product Lifecycle Management (PLM) Purchase",
    "summary": "OnLogic ECO to Purchase Customization.",
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
        "ol_purchase",
        "mrp_plm",
        "product_state",
        "purchase",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/mrp_eco_views.xml",
        "views/purchase_order_views.xml",
        "wizard/create_purchase_wizard.xml",
    ],
}
