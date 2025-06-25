# Import Python Libs
import json
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
    def _auth_method_ts_api(cls):
        """
        Validate the Tax & Shipping request based on the request's header, using SHA256 HMAC
        """

        # Get signature from the request header
        headers = request.httprequest.environ
        received_signature = headers.get("HTTP_X_ODOO_API_SIGNATURE")

        try:

            # Get the Request data
            request_data = request.get_json_data()
            if not request_data:
                # We need a valid data to be able to continue
                return Response("GraphQL Validation Failed: Invalid query data", status=403)

            # Get the related API Key from the client
            client_name = html_escape(request.httprequest.headers.get("X-Odoo-Api-Client", False))

            api_client_id = request.env["api.client"].search([("name", "=", client_name)])
            # Generate the signature based on the Api Clients api_key and the received query
            expected_signature = request.env["api"].generate_hmac_signature(
                key=api_client_id.api_key, data=request_data
            )
            received_signature = headers.get("HTTP_X_ODOO_API_SIGNATURE")
            if received_signature != expected_signature:
                _logger.error("TS API | Access denied! Invalid ODOO_API_SIGNATURE!")
                raise AccessDenied()
            
            # return super()._auth_method_public()
            # If we got to this point we confirmed that the Request is correct
            if request.env.uid is None:
                ts_user = request.env.ref("base.user_root")
                # Take the identity of the API key user
                request.update_env(user=ts_user.id)
                # Switch to the user context
                request.update_context(**request.env.user.context_get())
        except AccessDenied:
            raise
        except Exception as error:
            _logger.exception(f"TS API | Error during request validation | Error: {error}")
            raise error
