# Import Python libs
import json
import logging

# Import Odoo libs
from odoo import http
from odoo.addons.ol_graphql.controllers.main import GraphQLController
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ApiController(GraphQLController):
    @http.route("/graphiql/onlogic/main", auth="user")
    def graphiql(self, **kwargs):
        """
        Add User permission check to the graphiql endpoint
        """
        if not http.request.env.user.user_has_groups("ol_graphql.graphql_query"):
            _logger.warning(
                f"GraphQL Error: Access denied! User `{http.request.env.user.name} ({http.request.env.user})"
                " has no permission to access graphiql endpoint!"
            )
            raise AccessDenied()
        return super().graphiql(**kwargs)

    # Change the the auth method to `api_client`
    @http.route("/graphql/onlogic/main", auth="api_client", csrf=False)
    def graphql(self, **kwargs):
        """
        @ol_upgrade: Original decorator used in ol_graphql:
        @http.route("/graphql/onlogic/main", auth="user", csrf=False)
        """

        # Add a new context variable so we know the authentication was successful
        context = http.request.env.context.copy()
        context.update({"graphql_api_client_signature_validated": True})
        http.request.env.context = context

        res = super().graphql(**kwargs)

        # Do some basic response validation
        json_data = json.loads(res.data.decode("utf8"))

        if "errors" in json_data:
            _logger.error(
                f"GraphQL Error: `/graphql/onlogic/main` returned Status: `{res.status}`. Errors:"
                f" {json_data.get('errors', 'No Error Data')}"
            )

        return res
