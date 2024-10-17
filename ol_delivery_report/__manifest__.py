{
    "name": "OnLogic Delivery Reports",
    "summary": "Delivery Report Customizations",
    "description": """Delivery Report Customizations""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Inventory",
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_blind_dropship",
        "ol_sale",
        "stock",
    ],
    # always loaded
    "data": [
        "report/packing_slip_report.xml",
        "report/picking_slip_report.xml",
    ],
}
