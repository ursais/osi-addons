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
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "sale_margin",
        "sale_blanket_order",
        "base_tier_validation",
        "base_tier_validation_formula",
    ],
    # always loaded
    "data": [
        "security/tier_validation_group.xml",
        "views/tier_definition_view.xml",
        "data/tier_definition.xml",
    ],
    # only loaded in demo mode
    "demo": [
        "demo/res_users.xml",
    ],
    "application": False,
    "installable": True,
}
