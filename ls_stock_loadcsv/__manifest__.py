# pylint: disable=pointless-statement
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
        "base",
        "delivery",
        "stock",
        # "ls_base",
        # "ls_blind_dropship",
        # "ls_delivery",
        # "ls_delivery_account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/csv_loader_wizard_view.xml",
        "views/stock.xml",
        "views/delivery.xml",
        "views/partner.xml",
    ],
}
