{
    "name": "OnLogic Sale Booking",
    "summary": "Adds logic to log sale order total amount changes and booking information",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sale",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    # any module necessary for this one to work correctly
    "depends": [
        "ol_base",
        "ol_sale",
        "sale",
        "sale_blanket_order",
    ],
    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/sale_blanket_order_views.xml",
        "views/sale_booking_views.xml",
        "views/sale_order_views.xml",
    ],
}
