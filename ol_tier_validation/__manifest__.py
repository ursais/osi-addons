{
    "name": "Onlogic Tier Validation",
    "summary": """
        Extends the functionality of tier validation process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": [
        "base_tier_validation",
        "base_tier_validation_formula",
    ],
    # always loaded
    "data": [
        "security/tier_validation_group.xml",
        "views/tier_definition_view.xml",
    ],
    "application": False,
    "installable": True,
}
