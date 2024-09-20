{
    "name": "Onlogic Sale Tier Validation",
    "summary": """
        Extends the functionality of sale tier validation process.
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
        "sale_tier_validation",
    ],
    # always loaded
    "data": [],
    # only loaded in demo mode
    "demo": [],
    "application": False,
    "installable": True,
}
