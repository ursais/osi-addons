{
    "name": "Onlogic CRM to Estimate",
    "summary": "Create Estimates from CRM Opportunities.",
    "description": """Create Estimates from CRM Opportunities.""",
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "CRM",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "crm",
        "job_cost_estimate_customer",
    ],
    # Data Loaded.
    "data": [
        "views/crm_lead_views.xml",
        "views/sale_estimate_views.xml",
    ],
}
