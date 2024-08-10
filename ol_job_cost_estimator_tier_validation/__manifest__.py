{
    "name": "Onlogic Estimation for Jobs - Material / Labour / Overheads Tier Validation",
    "summary": """
        Extends the functionality of your Customers for materials, labour, overheads details in job estimation to support a tier validation process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "job_cost_estimate_customer",
        "base_tier_validation",
    ],
    # always loaded
    "data": [
        "views/sale_estimate_views.xml",
    ],
    "application": False,
    "installable": True,
}
