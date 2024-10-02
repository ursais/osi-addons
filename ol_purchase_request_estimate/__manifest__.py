{
    "name": "Onlogic Purchase Request Estimate",
    "summary": "Create Purchase Requests from Estimates.",
    "description": """Create Purchase Requests from Estimates.""",
    "author": "Onlogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Stock",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # Modules required to this module to work properly
    "depends": [
        "ol_base",
        "purchase_request",
        "job_cost_estimate_customer",
    ],
    # Data Loaded.
    "data": [
        "views/purchase_request_views.xml",
        "views/sale_estimate_views.xml",
    ],
}
