{
    "name": "MRP Sequence",
    "summary": "MRP Sequence",
    "description": """
    Adds Sequences to Manufacturing, scheduled start changes based on sequence.
    """,
    "author": "Open Source Integrators",
    "website": "https://www.opensourceintegrators.com",
    "onlogic": True,
    "category": "Manufacturing",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "mrp_batch",
    ],
    # always loaded
    "data": [
        "views/mrp_production_views.xml",
    ],
}
