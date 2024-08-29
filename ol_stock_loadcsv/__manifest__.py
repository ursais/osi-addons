{
    "name": "Create Delivery Orders from CSV import",
    "onlogic": True,
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "category": "Warehouse",
    "summary": "Create delivery orders for consigned stock from a csv",
    "depends": [
        "ol_base",
        "ol_blind_dropship",
        "delivery",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/csv_loader_wizard_view.xml",
        "views/stock.xml",
        "views/delivery.xml",
        "views/partner.xml",
    ],
}
