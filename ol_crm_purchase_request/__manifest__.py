{
    "name": "Onlogic CRM Purchase",
    "summary": "CRM Enhancements.",
    "description": """CRM Enhancements.""",
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "CRM",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "ol_purchase_request_estimate",
        "ol_crm",
    ],
    # Data Loaded.
    "data": [
        "views/crm_lead_views.xml",
        "views/purchase_request_view.xml",
    ],
}
