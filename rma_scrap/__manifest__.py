{
    "name": "RMA Scrap",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Allows to scrap the received/ordered products in odoo",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow",
    "depends": ["rma"],
    "data": [
        "security/ir.model.access.csv",
        "views/rma_operation_view.xml",
        "views/rma_order_line_view.xml",
        "views/rma_order_view.xml",
        "views/stock_scrap_view.xml",
        "wizards/rma_scrap_view.xml",
    ],
    "installable": True,
}
