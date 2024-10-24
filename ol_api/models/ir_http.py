# Import Python Libs
import logging
from werkzeug.wrappers import Response

# Import Odoo Libs
from odoo import models
from odoo.http import request
from odoo.tools import html_escape
from odoo.exceptions import AccessDenied
from odoo.addons.graphql_base import GraphQLControllerMixin


_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_api_client(cls):
        """
        Validate the GraphQL request based on the request's header, using SHA256 HMAC
        """

        # Get signature from the request header
        headers = request.httprequest.environ
        received_signature = headers.get("HTTP_X_ODOO_API_SIGNATURE")

        # The request body using oca/rest-framework/graphql_base/controllers/main.py _parse_body()
        # We add `False` as an attribute, we need to do this as `_parse_body()`
        # is not correctly marked as a @staticmethod so it expects `self` as a function attribute
        body = GraphQLControllerMixin._parse_body(False)

        data = body.get("query", False)
        if not data:
            # We need a valid data to be able to continue
            return Response("GraphQL Validation Failed: Invalid query data", status=403)

        # Get the related API Key from the client
        client_name = html_escape(
            request.httprequest.headers.get("X-Odoo-Api-Client", False)
        )

        api_client_id = request.env["api.client"].search([("name", "=", client_name)])

        # Generate the signature based on the Api Clients api_key and the received query
        expected_signature = request.env["api"].generate_hmac_signature(
            key=api_client_id.api_key, msg=data
        )

        if received_signature != expected_signature:
            _logger.error(
                "GraphQL Error: Access denied! Request could not be validated! Invalid signature!"
            )
            raise AccessDenied()

        # If we got to this point we confirmed that the GraphQL request is correct
        # So we can continue with the simirarly if the controller route would have been defined with `auth="public"`
        super(IrHttp, cls)._auth_method_public()
