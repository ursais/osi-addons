# pylint: disable=pointless-statement
{
    "name": "OnLogic Queue Job",
    "summary": "Adds OnLogic based enhancements to the OCA module `queue_job`",
    "version": "1.0",
    "depends": [
        "queue_job",
        "ol_base",
    ],
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "onlogic": True,
    "category": "Tools",
    "description": "Adds OnLogic based enhancements to the OCA module `queue_job`",
    "data": [
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "views/res_config_settings_views.xml",
        "data/ir_config_parameter.xml",
    ],
}
