# pylint: disable=pointless-statement
{
    # Used to filter our modules from various CLI functionality
    "onlogic": True,
    "name": "OnLogic Base",
    "summary": """Base OnLogic Module """,
    "description": """
        This is the core OnLogic Module.  It should not have much or any functionality, but
        all other modules should depend on it.
    """,
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "category": "Technical Settings",
    "version": "1.5",
    # any module necessary for this one to work correctly
    "depends": [
        "account_accountant",
        "account_consolidation",
        "approvals",
        "calendar",
        "contacts",
        "crm",
        "delivery_fedex",
        "delivery_ups",
        "delivery_usps",
        "documents",
        "helpdesk",
        "hr",
        "hr_contract",
        "hr_expense",
        "hr_skills",
        "knowledge",
        "mail",
        "maintenance",
        "mrp",
        "mrp_plm",
        "planning",
        "project",
        "project_todo",
        "purchase",
        "quality_control",
        "repair",
        "room",
        "sale_management",
        "sale_subscription",
        "stock",
        "stock_barcode",
        "timesheet_grid",
    ],
    # always loaded
    "data": [
        "data/company_data.xml",
        "data/product_data.xml",
        "views/res_company.xml",
    ],
    # only loaded in demonstration mode
    "demo": [
        # configurations
        # "demo/config/master_config.xml",
        # core records
        "demo/res/users.xml",
        "demo/res/groups.xml",
        "demo/res/partner.xml",
        "demo/res/currency.xml",
        # mail
        "demo/mail/server.xml",
        # accounting
        "demo/account/product.xml",
        "demo/account/payment_term.xml",
        "demo/account/payment_method.xml",
        # products
        "demo/product/attribute.xml",
        "demo/product/components.xml",
        # "demo/product/categories.xml", # Needs work
        # "demo/product/system.xml", # Needs work
        # "demo/product/supplierinfo.xml",  # Needs work
        # units of measure
        "demo/uom/uom.xml",
        # inventory
        "demo/stock/warehouse.xml",
        # "demo/stock/locations.xml",  # Needs work
        # "demo/stock/orderpoint.xml",  # Needs work
        # delivery
        "demo/delivery/carrier.xml",
        # crm
        "demo/crm/lead.xml",
        # accounting properties
        # "demo/ir/partner_properties.xml", # Needs work
        # "demo/ir/product_properties.xml", # Needs work
        # config parameters
        # "demo/ir/config_parameter.xml", #Will enable if m2x is desired
        # actions which need to be called (ie changing base records once)
        "demo/action/cron.xml",
    ],
}