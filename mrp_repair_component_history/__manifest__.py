{
    "name": "Manufacturing/Repair Component History",
    "description": """
        Show history of component changes on a serial number.
    """,
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "Manufacturing/Repairs",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "mrp",
        "repair",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/component_history_views.xml",
        "views/stock_lot_views.xml",
        "views/repair_views.xml",
    ],
    "installable": True,
}
