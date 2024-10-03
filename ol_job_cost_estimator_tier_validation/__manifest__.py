{
    "name": "Onlogic Sale Estimates Tier Validation",
    "summary": """
        Extends the functionality of your Customers for materials, labour,
        overheads details in job estimation to support a tier validation process.
        """,
    "author": "OnLogic, Open Source Integrators",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_tier_validation",
        "job_cost_estimate_customer",
        "base_tier_validation",
    ],
    # always loaded
    "data": [
        "data/tier_job_estimator_def_data.xml",
        "views/sale_estimate_views.xml",
    ],
    "application": False,
    "installable": True,
}
