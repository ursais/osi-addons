# Import Python libs
import logging
from functools import partial
from time import time as timer
from graphql_server import (
    HttpQueryError,
    encode_execution_results,
    format_error_default,
    json_encode,
    run_http_query,
)

# Import Odoo libs
from odoo import http
from odoo.addons.ol_graphql.schema import onlogic_schema
from odoo.addons.graphql_base import GraphQLControllerMixin
from odoo.exceptions import ValidationError
from odoo.tools import config

_logger = logging.getLogger(__name__)


def graphql_timing_middleware(next, root, info, **args):
    """
    Print any processes that take longer than 100ms
    """
    start = timer()
    return_value = next(root, info, **args)
    duration = round((timer() - start) * 1000, 2)
    if duration > 100:
        _logger.info(
            f"GraphQL Mutation | TIMING | {info.parent_type.name} | Duration: {duration} ms | Field:{info.field_name}"
        )
    return return_value


class GraphQLController(http.Controller, GraphQLControllerMixin):
    """
    This whole file copied from oca/rest-framework/graphql_demo/controllers/main.py
    """

    # The GraphiQL route, providing an IDE for developers
    @http.route("/graphiql/onlogic/main", auth="user")
    def graphiql(self, **kwargs):
        if not http.request.env["ir.config_parameter"].get_as_boolean(
            "ol_graphql.graphql_enabled"
        ) or config.get("odoo_upgrade_instance", False):
            raise ValidationError(
                "Odoo GraphQL is"
                f" disabled{' on Upgrade Instances' if config.get('odoo_upgrade_instance', False) else ''}!"
            )
        return self._handle_graphiql_request(onlogic_schema.schema.graphql_schema)

    # The graphql route, for applications.
    # Note csrf=False: you may want to apply extra security
    # (such as origin restrictions) to this route.
    @http.route("/graphql/onlogic/main", auth="user", csrf=False)
    def graphql(self, **kwargs):
        if not http.request.env["ir.config_parameter"].get_as_boolean(
            "ol_graphql.graphql_enabled", False
        ) or config.get("odoo_upgrade_instance", False):
            raise ValidationError(
                "Odoo GraphQL is"
                f" disabled{' on Upgrade Instances' if config.get('odoo_upgrade_instance', False) else ''}!"
            )
        return self._handle_graphql_request(onlogic_schema.schema.graphql_schema)

    def _process_request(self, schema, data):
        """
        Hook into the OCA module so we can inject middlewares to the GraphQL query calls
        """
        graphql_log_incoming_mutations = http.request.env[
            "ir.config_parameter"
        ].get_as_boolean("ol_graphql.graphql_log_incoming_mutations", False)

        if not graphql_log_incoming_mutations:
            return super()._process_request(schema=schema, data=data)

        # @ol_upgrade:  If the `graphql_log_incoming_mutations` setting is enabled,
        #               we want to inject the timing middleware in to the query execution
        try:
            request = http.request.httprequest
            execution_results, all_params = run_http_query(
                schema,
                request.method.lower(),
                data,
                query_data=request.args,
                batch_enabled=False,
                catch=False,
                context_value={"env": http.request.env},
                # @ol_upgrade(+1/0): Use the timing middleware
                middleware=[graphql_timing_middleware],
            )
            result, status_code = encode_execution_results(
                execution_results,
                is_batch=isinstance(data, list),
                format_error=format_error_default,
                encode=partial(json_encode, pretty=False),
            )
            headers = dict()
            headers["Content-Type"] = "application/json"
            response = http.request.make_response(result, headers=headers)
            response.status_code = status_code
            if any(er.errors for er in execution_results):
                env = http.request.env
                env.cr.rollback()
                env.clear()
            return response
        except HttpQueryError as e:
            result = json_encode({"errors": [{"message": str(e)}]})
            headers = dict(e.headers)
            headers["Content-Type"] = "application/json"
            response = http.request.make_response(result, headers=headers)
            response.status_code = e.status_code
            env = http.request.env
            env.cr.rollback()
            env.clear()
            return response
