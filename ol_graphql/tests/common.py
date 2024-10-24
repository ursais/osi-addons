# Import Python libs
import json
import werkzeug.datastructures
from unittest.mock import patch
from collections import OrderedDict
import logging
import uuid
from enum import Enum
import copy

_logger = logging.getLogger(__name__)

# Import Odoo libs
from odoo import http
from odoo.exceptions import ValidationError
from odoo.addons.ol_graphql.schema import onlogic_schema
from odoo.addons.ol_graphql.tests.validation import GQLUnitTestValidation
from odoo.addons.graphql_base import GraphQLControllerMixin
from odoo.addons.ol_base.tests.common import OnLogicBaseTransactionCase


class Operation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class OnLogicBaseGraphQLTransactionCase(
    OnLogicBaseTransactionCase, GQLUnitTestValidation
):
    """
    GraphQL unit testing framework
    """

    def setUp(self):
        super().setUp()
        # An instance of the Odoo class being tested (eg. self.env['sale.order'])
        self.odoo_record = False
        # The GraphQL object mutation operations
        # (eg. {Operation.CREATE: 'create_customer', Operation.UPDATE: 'update_customer'})
        self.mutation_operations = False
        # The GraphQL object query name (eg. sale_orders)
        self.query_name = False
        # The GraphQL object type (eg. SaleOrderType)
        self.schema_type = False
        # The GraphQL input type (eg. SaleOrderInput)
        self.input_type = False
        # The list of fields to query
        self.query_fields = False
        # A dict containing functions to call before a mutation
        self.additional_mutation_data_prep_funcs = False
        # Set which query result fields we should not validate
        self.validation_query_fields_to_skip = False
        # Set which query result fields we should validate
        self.validation_query_fields_to_validate = False
        # Set which mutation result fields we should not validate
        self.validation_mutation_fields_to_skip = False
        # Set which mutation result fields we should validate
        self.validation_mutation_fields_to_validate = False

    def make_graphql_request(self, gql_action_data, gql_action_name):
        """
        This function runs the real GraphQL Query or Mutation.
        We are not making an HTTP call to the Controller endpoint
        but directly call the highest level entry point method `_handle_graphql_request()`

        We mock out the HTTP request in a way that represents the real world request as much as possible.
        """

        with patch.object(http, "request") as mock_request:
            # Set up the mock odoo.http.request.httprequest
            class MockHttpRequest:
                def __init__(self):
                    self.mimetype = "application/json"
                    self.data = json.dumps(gql_action_data).encode("utf-8")
                    self.params = OrderedDict()
                    self.method = "POST"
                    self.args = werkzeug.datastructures.ImmutableOrderedMultiDict([])

            # Mock out the `make_response()` method so that we can easily extract the passed in GQL data
            def make_response_side_effect(*args, **kwargs):
                class MockHttpResponse:
                    def __init__(self, data, headers):
                        self.data = data
                        self.headers = headers
                        self.status_code = False

                response_result = json.loads(args[0])

                if response_result.get("errors", False):
                    raise ValidationError(
                        f"Error during UnitTest GraphQL: {response_result.get('errors', False)}"
                    )

                return MockHttpResponse(
                    data=response_result, headers=kwargs.get("headers", {})
                )

            # Set the mock request values
            # Add a new context variable so we know the authentication was successful
            # we mimic outside services calling into odoo GraphQL
            context = self.env.context.copy()
            context.update({"graphql_api_client_signature_validated": True})
            self.env.context = context
            mock_request.env = self.env
            mock_request.httprequest = MockHttpRequest()
            mock_request.make_response.side_effect = make_response_side_effect

            # Call the main GQL method that is used in the controllers
            result = GraphQLControllerMixin()._handle_graphql_request(
                schema=onlogic_schema.schema.graphql_schema
            )

        # Extract the results
        graphql_status_code = result.status_code
        graphql_result = result.data.get("data", False)

        return graphql_status_code, graphql_result.get(gql_action_name, False)

    def run_test(
        self,
        operation_type=Operation.CREATE,
        skip_query_validation=False,
        skip_mutation_validation=False,
        overwrite_uuid=False,
    ):
        """
        To make our life easier we use GQL query to get the object data in almost correct format
        to use it for mutations.

        1. Create an Odoo Record via Odoo ORM
        2. Query this record data via GQL
        3. Decode the received data to remove / alter some of the that needs to be unique data (name, uuid)
        4. Run mutation
        5. Query the newly created record via GraphQL
        6. Compare the created record against the mutation data and the original Odoo record
        """

        self.assertTrue(
            self.odoo_record, "Base Odoo record for the GraphQl unit test is missing!"
        )

        #######################
        # Query Related Tests #
        #######################

        # Run a GraphQL query against the base odoo record
        status_code, query_data = self.query_odoo_record()

        # Do some basic query validation
        self.validate_base_query_result(status_code, query_data)

        query_data = query_data[0]

        if not skip_query_validation:
            # Validate the details of the returned data
            self.validate_query_results(
                odoo_object=self.odoo_record,
                type_object=self.schema_type,
                gql_data=query_data,
            )

        ##########################
        # Mutation Related Tests #
        ##########################

        record_uuid = (
            str(uuid.uuid4())
            if operation_type == Operation.CREATE
            else query_data.get("uuid", False)
        )

        # We may want to overwrite the UUID, for example when running a CREATE mutation for a placeholder record
        if overwrite_uuid:
            record_uuid = overwrite_uuid

        # Get the mutation data
        mutation_data = self.prepare_mutation_data(query_data, record_uuid)

        if self.additional_mutation_data_prep_funcs:
            # Allow tests to do additional specific mutation preparation
            for (
                mutation_data_prep_func,
                mutation_data_prep_kwargs,
            ) in self.additional_mutation_data_prep_funcs.items():
                if hasattr(self, mutation_data_prep_func):
                    kwargs = mutation_data_prep_kwargs or {}
                    assert isinstance(
                        kwargs, dict
                    ), f"Args passed to mutation data prep function ({kwargs}) is not a dict!"
                    mutation_data = getattr(self, mutation_data_prep_func)(
                        mutation_data=mutation_data,
                        query_data=query_data,
                        **kwargs,
                    )

        # Run the GraphQL mutation
        mutation_status_code, _ = self.run_mutation(
            mutation_name=self.mutation_operations.get(operation_type),
            mutation_input_type=self.input_type,
            mutation_data=mutation_data,
        )

        # Make sure we get the correct status code
        self.assertEqual(
            mutation_status_code,
            200,
            f"GraphQL mutation resulted in wrong ({mutation_status_code}) status code!",
        )

        # Find the newly created record based on UUID
        new_odoo_record = self.env[self.odoo_record._name].get_by_uuid(record_uuid)

        # Test if the record was created successfully
        self.assertTrue(
            new_odoo_record,
            "No new Odoo record was created as a result of the GraphQL mutation!",
        )

        # Run a GraphQL query for the newly created Odoo record
        new_odoo_record_status_code, new_query_data = self.query_odoo_record(
            odoo_record=new_odoo_record
        )

        # Do some basic query validation
        self.validate_base_query_result(new_odoo_record_status_code, new_query_data)

        new_query_data = new_query_data[0]

        if not skip_query_validation:
            # Validate the details of the returned data
            self.validate_query_results(
                odoo_object=new_odoo_record,
                type_object=self.schema_type,
                gql_data=new_query_data,
            )

        if not skip_mutation_validation:
            self.validate_mutation_result(
                old_record=self.odoo_record,
                old_record_query_result=query_data,
                new_record=new_odoo_record,
                new_record_query_result=new_query_data,
                mutation_data=mutation_data,
            )

        return (
            self.odoo_record,
            query_data,
            mutation_data,
            new_odoo_record,
            new_query_data,
        )

    def query_odoo_record(self, odoo_record=False, query_fields=False):
        if not odoo_record:
            odoo_record = self.odoo_record

        if not query_fields:
            query_fields = self.query_fields

        # Run the GraphQL query
        return self.run_query(uuids=[odoo_record.uuid])

    def run_query(self, uuids, query_name=False, query_fields=False):
        # Use default if necessary
        query_name = query_name or self.query_name

        query_data = self.get_query_data(
            uuids=uuids, query_name=query_name, query_fields=query_fields
        )
        return self.make_graphql_request(
            gql_action_data=query_data, gql_action_name=query_name
        )

    def get_query_data(self, uuids, query_name, query_fields=False):
        """
        Create the GraphQL Query
        """

        query_string = query_fields or self.query_fields

        # The GraphQL query
        query = f"""
            query ObjectQuery($uuids: [String]!, $transaction_id: ID) {{
                {query_name}(uuids: $uuids, order: "id DESC", transaction_id: $transaction_id) {{
                    {query_string}
                }}
            }}
        """

        # Set the request payload
        query_data = {
            "query": query,
            "variables": {"uuids": uuids},
        }
        return query_data

    def validate_base_query_result(self, status_code, query_data):
        self.assertEqual(
            status_code,
            200,
            f"GraphQL query resulted in the wrong ({status_code}) status code!",
        )
        self.assertTrue(bool(query_data), "GraphQL query did not return any results!")
        self.assertTrue(
            len(query_data) == 1, "GraphQL query returned more than one result!"
        )

    def prepare_mutation_data(self, query_data, record_uuid):
        """
        Decode the query data to remove / alter some of the data that needs to be unique (eg. UUID)
        This function is intended to be overridden in later modules
        """
        mutation_data = {}
        mutation_fields = self.get_graphql_mutation_fields()

        for field, value in query_data.items():
            if field not in mutation_fields:
                continue
            # Use a unique record UUID
            if field == "uuid":
                mutation_data["uuid"] = record_uuid
                continue
            # Use the returned query data
            mutation_data[field] = value
        return mutation_data

    def get_graphql_mutation_fields():
        """
        The specific fields we want to use from the GraphQL query results for mutations
        This function is intended to be overridden in later modules
        """

    def run_mutation(self, mutation_name, mutation_input_type, mutation_data):
        mutation_data = self.get_mutation_data(
            mutation_name=mutation_name,
            mutation_input_name=mutation_input_type,
            mutation_data=mutation_data,
        )
        return self.make_graphql_request(
            gql_action_data=mutation_data,
            gql_action_name=mutation_name,
        )

    @staticmethod
    def get_mutation_data(mutation_name, mutation_input_name, mutation_data):
        """
        Create the GraphQL Mutation
        """

        mutation = f"""
             mutation ObjectMutation($data: {mutation_input_name}!) {{
                {mutation_name}(data: $data) {{
                    graphql_successful
                }}
            }}
        """

        # Set the request payload
        mutation_request_data = {
            "query": mutation,
            "variables": {"data": mutation_data},
        }

        return mutation_request_data

    def mutation_data_prep_change_field(self, mutation_data, **kwargs):
        # Mutation data may be an alias of the original query data, so make a deep copy
        mutation_data_copy = copy.deepcopy(mutation_data)
        fields_to_change = kwargs.get("fields_to_change", [])
        object_to_change = self.get_nested_object(
            mutation_data_copy, kwargs.get("nested_item_path", [])
        )
        change_type = kwargs.get("change_type", False)

        for kv in fields_to_change:
            field = kv.get("field", False)
            value = kv.get("value", False)
            object_to_change[field] = value

        if change_type == "pop":
            object_to_change.pop()
        if change_type == "append":
            if isinstance(object_to_change, dict):
                object_to_change.update(kwargs.get("value"))
            elif isinstance(object_to_change, list):
                object_to_change.append(kwargs.get("value"))
        return mutation_data_copy

    def get_nested_object(self, mutation_data, nested_item_path):
        # Use the nested item path to "dig in" to the JSON
        nested_item = mutation_data
        for key in nested_item_path:
            # 'key' can be either a dictionary key or a list index
            nested_item = nested_item[key]
        return nested_item
