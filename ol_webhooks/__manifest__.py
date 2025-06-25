# pylint: disable=pointless-statement
{
    "name": "OnLogic Webhooks",
    "summary": "Adds the possibility to create webhooks that can be called on predefined events.",
    "version": "1.0",
    "license": "AGPL-3",
    "depends": [
        "ol_base",
        "ol_api",
        "ol_queue_job",
        "ol_uuid",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "description": """Adds the possibility to create webhooks that can be called on predefined events.""",
    "data": [
        # "data/api_clients.xml",
        "data/invoice.xml",
        "data/ir_config_parameter.xml",
        "data/ir_cron.xml",
        "data/mrp_bom.xml",
        "data/mrp_production.xml",
        "data/partner.xml",
        "data/product.xml",
        "data/queue_job_channel.xml",
        # "data/rma.xml", TODO: (4/23/2025) Waiting for business sign off on RMA solution
        # "data/sale_booking.xml", TODO: (4/23/2025) Waiting for OSI to finish sale bookings development
        "data/sale_order.xml",
        # "data/stock_picking.xml", TODO: (4/23/2025) Waiting for OnLogic development of tracking numbers
        # "data/support_repair_order.xml", TODO: (4/23/2025) Waiting for business sign off on RMA solution
        "security/ir.model.access.csv",
        "views/account_move.xml",
        "views/api_clients.xml",
        "views/mrp_bom.xml",
        # "views/product_template.xml", TODO: (4/23/2025) Waiting for product stock queue implementation
        # "views/repair_order.xml", TODO: (4/23/2025) Waiting for business sign off on RMA solution
        "views/res_config_settings_views.xml",
        "views/res_partner.xml",
        # "views/rma.xml", TODO: (4/23/2025) Waiting for business sign off on RMA solution
        "views/sale_order.xml",
        "views/webhooks.xml",
        "views/webhooks_events.xml",
    ],
}
