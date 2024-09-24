{
    "name": "Onlogic Sale Estimates Customer",
    "summary": """
        Extends the functionality of your Customers for materials, labour,
        overheads details in job estimation to support a Customer process.
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
        "job_cost_estimate_customer",
    ],
    # always loaded
    "data": [
        "views/sale_estimate_views.xml",
    ],
    "application": False,
    "installable": True,
}
