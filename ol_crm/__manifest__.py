{
    "name": "Onlogic CRM",
    "summary": "CRM Enhancements.",
    "description": """CRM Enhancements.""",
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "CRM",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": ["ol_base", "sale_crm",],
    # Data Loaded.
    "data": [
        "data/sale_team_data.xml",
        "data/crm_stage_data.xml",
        "views/crm_lead_views.xml",
        "views/crm_stage_views.xml",
    ],
}
