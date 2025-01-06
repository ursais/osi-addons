{
    "name": "Onlogic CRM MRP PLM",
    "summary": """
        Adds the ability to create ECO from the Opportunity.
        """,
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "CRM",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "ol_job_cost_estimate_customer",
        "crm",
    ],
    # Data Loaded.
    "data": [
        "views/crm_lead_views.xml",
        "views/mrp_eco_view.xml",
    ],
}
