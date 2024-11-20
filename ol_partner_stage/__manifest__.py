{
    "name": "Onlogic Partner Stage",
    "summary": "Onlogic Partner Stage Customizations",
    "description": """
    Onlogic Partner Stage Customizations
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Contacts",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "partner_stage",
    ],
    # always loaded
    "data": [
        "data/partner_stage_data.xml",
    ],
}
