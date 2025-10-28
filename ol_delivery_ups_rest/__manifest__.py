# -*- coding: utf-8 -*-
{
    "name": "OnLogic - UPS Shipping",
    "summary": "Modifications to the enterprise UPS Shipping module",
    "category": "Inventory/Delivery",
    "version": "17.0.0.1.0",
    "application": True,
    "onlogic": True,
    "depends": ["delivery_ups_rest", "ol_delivery"],
    "data": [
        "views/delivery_carrier.xml",
        "views/sale_order.xml",
        "views/stock_package_type.xml",
        "views/stock_picking.xml",
        "views/res_company.xml",
    ],
    "license": "AGPL-3",
}
