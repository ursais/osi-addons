# Import Python libs
import graphene
from enum import Enum
from graphene.types.objecttype import ObjectTypeMeta

# Import Odoo libs
from odoo import fields
from odoo.exceptions import ValidationError


class GQLUnitTestValidation:
    def validate_query_results(self, odoo_object, type_object, gql_data):
        """
        Validate the field values for the given Odoo object are matching
        between the GQL result and Odoo
        """

        # We should never validate Transaction ID as they should be unique by design
        fields_to_skip = self.validation_query_fields_to_skip or ["transaction_id"]
        if "transaction_id" not in fields_to_skip:
            fields_to_skip.append("transaction_id")

        for field_name, field_value in gql_data.items():

            if (
                self.validation_query_fields_to_validate
                and field_name not in self.validation_query_fields_to_validate
            ):
                # If we only need to validate certain fields
                # and the current one is not included skip it
                continue

            if fields_to_skip and field_name in fields_to_skip:
                # We don't want to validate certain fields
                continue

            odoo_object_value = self.get_odoo_object_value(
                odoo_object=odoo_object, type_object=type_object, field_name=field_name
            )

            if not field_value:
                # If the value is not set we can do a direct comparison
                self.validate_direct_compare(
                    odoo_object, field_name, field_value, odoo_object_value
                )
                return

            validate_function_name = f"validate_query_field_{field_name}"
            if hasattr(self, validate_function_name):
                # If there is a specific validation function defined that
                getattr(self, validate_function_name)(
                    odoo_object, odoo_object_value, field_name, field_value
                )
                continue

            if (
                self.is_graph_object_field(type_object, field_name)
                and field_value
                and odoo_object_value
            ):
                # Object fields would be to complicated to decode in a generic way
                # so we are skipping them.
                # If you would like to validate them
                # you need to use a specific `f"validate_query_field_{field_name}"` function
                continue

            # Do a simple direct comparison
            self.validate_direct_compare(
                odoo_object, field_name, field_value, odoo_object_value
            )

    def validate_direct_compare(
        self, odoo_object, field_name, field_value, compare_field_value, error_msg=False
    ):
        if not error_msg:
            error_msg = (
                f"{odoo_object._name} graphql query result for field `{field_name}` is incorrect! GQL Value:"
                f" {field_value} Odoo Value: {compare_field_value}"
            )
        self.assertEqual(
            self.get_false_to_none_or_value(field_value),
            self.get_false_to_none_or_value(compare_field_value),
            error_msg,
        )

    @staticmethod
    def get_false_to_none_or_value(value):
        """
        Convert False to None or just return the value
        """
        return None if value is False else value

    def validate_mutation_result(
        self,
        old_record,
        old_record_query_result,
        new_record,
        new_record_query_result,
        mutation_data,
    ):

        # We should never validate Transaction ID as they should be unique by design
        fields_to_skip = self.validation_mutation_fields_to_skip or ["transaction_id"]
        if "transaction_id" not in fields_to_skip:
            fields_to_skip.append("transaction_id")

        for field_name, mutation_query_value in mutation_data.items():
            # Loop over the mutation query and make sure the values on the record are correct

            if (
                self.validation_mutation_fields_to_validate
                and field_name not in self.validation_mutation_fields_to_validate
            ):
                # If we only need to validate certain fields
                # and the current one is not included skip it
                continue

            if fields_to_skip and field_name in fields_to_skip:
                # We don't want to validate certain fields
                continue

            old_query_field_value = old_record_query_result.get(field_name, False)
            new_record_query_field_value = new_record_query_result.get(
                field_name, False
            )

            validate_function_name = f"validate_mutation_field_{field_name}"
            if hasattr(self, validate_function_name):
                getattr(self, validate_function_name)(
                    field_name,
                    mutation_query_value,
                    new_record_query_field_value,
                    old_query_field_value,
                    old_record,
                    new_record,
                )
                continue

            self.assertEqual(
                self.get_false_to_none_or_value(mutation_query_value),
                self.get_false_to_none_or_value(new_record_query_field_value),
                f"Mutation record `{new_record._name}` has incorrect value for field: `{field_name}` is"
                " incorrect!",
            )

    def get_odoo_object_value(self, odoo_object, type_object, field_name):
        """
        Get the given field value from the resolver function
        or fall back reading directly from the Odoo Object

        We make sure to convert `False` to `None` to match the GQL schema
        """
        if not odoo_object:
            raise ValidationError("Can't get Odoo Object value as object is missing!")

        odoo_field_value = None
        resolver_function_name = f"resolve_{field_name}"

        if hasattr(type_object, resolver_function_name):
            # Use the related GraphQL Type objects resolver function.
            # From a testing perspective it's not really useful
            # to use the same function to generate the data we validate against
            # that also generated the data we want to validate in the first place.
            # At least we are not skipping the fields and are doing some basic sanity checking.
            odoo_field_value = getattr(type_object, resolver_function_name)(
                odoo_object, None
            )
        elif hasattr(odoo_object, field_name):
            # Fall back getting the field value directly from the object
            odoo_field_value = getattr(odoo_object, field_name)
        else:
            raise ValidationError(
                f"Odoo Object {odoo_object._name} does not have field: {field_name} and related GraphQL type"
                f" object doesn't have resolver function: {resolver_function_name}"
            )

        return self.decode_odoo_value(type_object, field_name, odoo_field_value)

    def decode_odoo_value(self, type_object, field_name, odoo_field_value):
        # Convert and decode the gql_field_value or object_value
        graphql_field = getattr(type_object, field_name)
        if issubclass(type(odoo_field_value), Enum):
            # We need to handle enumerated fields differently
            odoo_field_value = odoo_field_value.value.upper()

        if issubclass(type(graphql_field), graphene.DateTime):
            # Convert Datetime
            odoo_field_value = fields.Datetime.to_string(odoo_field_value)

        if issubclass(type(graphql_field), graphene.Date):
            # Convert Date
            odoo_field_value = fields.Date.to_string(odoo_field_value)

        return odoo_field_value

    @staticmethod
    def is_graph_object_field(type_object, field_name):
        """
        Check if this field is for an other GraphQL Object. Ex.: Customer, Product etc,
        """
        field = getattr(type_object, field_name)
        if issubclass(type(field), graphene.List):
            # If this is a list check what the field types are the list made of
            return issubclass(type(field.of_type), ObjectTypeMeta)
        return hasattr(field, "type") and issubclass(type(field.type), ObjectTypeMeta)
