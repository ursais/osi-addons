# pylint: disable=pointless-statement
{
    "name": "OnLogic Tax & Shipping API",
    "summary": (
        "Adds feature to use Odoo as an API endpoint to gather Avatax Tax, VAT and Shipping information based"
        " on ecommerce cart data"
    ),
    "version": "17.0.0.1.0",
    "license": "AGPL-3",
    "depends": [
        "ol_base",
        "ol_api",
        "ol_uuid",
        "delivery",
        "ol_delivery",
        "ol_graphql_sale",
        "account_avatax_oca",
        "ol_delivery_ups_rest",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "application": True,
    "category": "Integrations",
    "description": """Adds feature to use Odoo as an API endpoint to gather Avatax Tax, VAT and Shipping information based on ecommerce cart data""",
    "data": [
        "data/res_users.xml",
        'views/delivery_carrier.xml',
    ],
    # 'post_init_hook': '_migrate_delivery_carrier_uuid_field',
}
