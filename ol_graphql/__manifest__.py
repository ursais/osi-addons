# pylint: disable=pointless-statement
{
    "name": "OnLogic GraphQL Integration",
    "summary": "OnLogic graphql controllers and endpoints",
    "description": """
    Using the OCA's graphql_base code, this module sets up the necessary endpoints
    and graphql schemas
    """,
    "author": "OnLogic",
    "onlogic": True,
    # While this the core OnLogic GraphQL module we are marking as `graphql`
    # because it does not contain GraphQL definitions
    "graphql": False,
    "website": "https://www.onlogic.com",
    "category": "API",
    "version": "1.0",
    "depends": [
        "graphql_base",
        "ol_base",
        "ol_queue_job",
        "ol_uuid",
    ],
    "data": [
        "data/ir_cron.xml",
        "data/queue_job_channel.xml",
        "security/ir.model.access.csv",
        "security/res_groups.xml",
        "views/res_config_settings_views.xml",
        "views/graphql_queue.xml",
        "views/queue_job_views.xml",
        "data/ir_config_parameter.xml",
    ],
}
