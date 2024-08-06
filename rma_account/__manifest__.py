# Copyright 2017 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Account",
    "version": "17.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Integrates RMA with Invoice Processing",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow",
    "depends": ["stock_account", "rma"],
    "data": [
        "security/ir.model.access.csv",
        "data/rma_operation.xml",
        "views/rma_order_view.xml",
        "views/rma_operation_view.xml",
        "views/rma_order_line_view.xml",
        "views/account_move_view.xml",
        "views/rma_account_menu.xml",
        "wizards/rma_add_account_move.xml",
        "wizards/rma_refund.xml",
    ],
    "installable": True,
}
