# Import Odoo libs
from odoo import fields, models


class GraphQLSettings(models.TransientModel):
    """
    Handles default Product GraphQL Search settings.
    """

    _inherit = "res.config.settings"

    # COLUMNS #######
    graphql_enabled = fields.Boolean(
        string="Enabled",
        help="Main switch to enable or disable Odoo GraphQL",
        config_parameter="ol_graphql.graphql_enabled",
    )
    graphql_update_from_create = fields.Boolean(
        string="Update from Create",
        help="If create mutation received for an existing record, consider it as an update mutation.",
        config_parameter="ol_graphql.graphql_update_from_create",
    )
    graphql_create_from_update = fields.Boolean(
        string="Create from Update",
        help="If update mutation received for a non existing record, consider it as a create mutation.",
        config_parameter="ol_graphql.graphql_create_from_update",
    )
    graphql_use_placeholders = fields.Boolean(
        string="Use Placeholders",
        help=(
            "If the received mutation is referring to related records that don't exist, instead of rejecting"
            " the request try to create placeholders."
        ),
        config_parameter="ol_graphql.graphql_use_placeholders",
    )
    graphql_log_incoming_mutations = fields.Boolean(
        string="Log Incoming Mutations",
        help=("Log the incoming GraphQL mutation queries"),
        config_parameter="ol_graphql.graphql_log_incoming_mutations",
    )
    graphql_log_query_timing = fields.Boolean(
        string="Log Query Timing",
        help=("Logs the amount of time it takes to finish GraphQL queries"),
        config_parameter="ol_graphql.graphql_log_query_timing",
    )

    # END #########
