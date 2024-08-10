{
    "name": "Onlogic PLM ECO Tier Validation",
    "summary": """
        Extends the functionality of PLM ECO to support a tier validation process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "mrp_plm",
        "base_tier_validation",
        "ol_mrp_plm_cancel",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/plm_eco_stage_views.xml",
        "views/plm_eco_view.xml",
    ],
    "application": False,
    "installable": True,
}
