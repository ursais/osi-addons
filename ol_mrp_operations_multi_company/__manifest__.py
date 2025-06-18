{
    "name": "OnLogic MRP Operations Multi-Company",
    "summary": "Allow global BoMs and company-specific operations/workcenters",
    "description": """Allow global BoMs and company-specific operations/workcenters""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "MRP",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "mrp",
    ],
    # always loaded
    "data": [
        # "views/mrp_production_view.xml",
    ],
}
