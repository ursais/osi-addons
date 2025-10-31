# pylint: disable=pointless-statement
{
    "name": "OnLogic Product System Stock",
    "summary": "Handles the functionality around a new high level System Stock field",
    "version": "1.0",
    "depends": [
        "ol_base",
        "ol_product",
        "ol_mrp_plm",
        "ol_api",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Sales",
    "description": "Handles the functionality around a new high level System Stock field",
    "data": [
        "data/ir_cron.xml",
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "views/product_stock_queue.xml",
        "wizard/result_wizard.xml",
    ],
    "post_init_hook": "_run_install_scripts",
}
