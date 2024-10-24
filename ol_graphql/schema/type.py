# Import Python Libs
import logging
import graphene
import uuid as uuid_lib
from enum import Enum
from graphql import GraphQLError

# Import Odoo libs
from graphene.types.generic import GenericScalar
from odoo.addons.graphql_base import OdooObjectType
from odoo.exceptions import ValidationError, AccessError, AccessDenied

_logger = logging.getLogger(__name__)


class CompanyEnum(Enum):
    """
    Enumeration for valid companies
    """

    US = "us"
    EU = "eu"

    def get_odoo_company_user(self, env):
        return (
            env["res.company"]
            .sudo()
            .search([("short_name", "=", self.value)], limit=1)
            .company_user_id
        )


CompanyEnumType = graphene.Enum.from_enum(CompanyEnum)


class UUID(graphene.String):
    """
    UUID Type to provide validation
    """

    @staticmethod
    def validate(uuid_val):
        """
        Validate a UUID
        """
        return uuid_lib.UUID(uuid_val)


class OnLogicBaseObjectType(OdooObjectType):
    """
    Add generic fields that every object should use
    """

    active = graphene.Boolean()
    uuid = graphene.ID(required=False)
    ordering_key = graphene.ID(required=True)
    transaction_id = graphene.ID(required=True)
    message_source = graphene.String(required=True)
    origin_system = graphene.String(required=False)
    odoo_url = graphene.String(required=False)
    locale = graphene.String(required=False)
    date_data = GenericScalar()

    @staticmethod
    def resolve_active(odoo_record, _):
        """
        Try to get the `active` field from the related Odoo record
        id the field doesn't exists we can safely default to True
        """
        if not odoo_record._fields.get("active", False):
            return True
        return odoo_record.active

    @staticmethod
    def resolve_uuid(odoo_record, _):
        """
        Try to get the UUID from the related Odoo record
        """
        if not odoo_record._fields.get("uuid", False):
            raise GraphQLError(f"UUID not implemented for `{odoo_record._name}`")
        return odoo_record.uuid or None

    @staticmethod
    def resolve_locale(odoo_record, _):
        """
        Get the records locale
        """
        locale = None
        if hasattr(odoo_record, "lang"):
            locale = getattr(odoo_record, "lang")
        return locale or None

    @staticmethod
    def resolve_ordering_key(odoo_record, info):
        """
        The ordering key should match the UUID of the record
        """
        return OnLogicBaseObjectType.resolve_uuid(odoo_record, info)

    @staticmethod
    def resolve_transaction_id(odoo_record, _):
        """
        Return the received transaction_id or
        generate it which is just a new UUID
        """
        transaction_id = odoo_record.env.context.get("transaction_id", False)
        return transaction_id or uuid_lib.uuid4()

    @staticmethod
    def resolve_message_source(odoo_record, _):
        """
        Set the message_source as `odoo`
        """
        return "odoo"

    @staticmethod
    def resolve_origin_system(odoo_record, _):
        """
        Set the origin_system as `odoo`
        """
        if not odoo_record._fields.get("origin_system", False):
            # If the records doesn't implement the `graphql.mixin` throw an error
            _logger.error(
                f"GraphQL Error: `origin_system` not implemented for `{odoo_record._name}`"
            )
        # Send the value or default to 'odoo'
        return odoo_record.origin_system or None

    @staticmethod
    def get_company_dependent_field_value(
        base_record, field_name=False, relations=False
    ):
        """
        Get the given field from the record (or return the record it self), possibly from a related record
        """
        if not base_record:
            raise ValidationError(
                f"GraphQL error: Invalid values received. `record`: `{base_record}` is missing"
            )

        values = []
        companies = base_record.env["res.company"].get_all()
        for company in companies:
            # Get the order to get the company specific info
            try:
                # Prepare the record to be read with the correct company
                record = base_record.with_user(company.company_user_id).with_company(
                    company.id
                )

                # If relations were defined get the correct related record
                record = record.mapped(relations) if relations else record

                # Read the field value from the record
                if field_name:
                    site_value = getattr(record, field_name)
                else:
                    site_value = record

                # If the field is not Boolean, and is not set we should return `null` rather then `False`
                if not site_value and (
                    not field_name or record._fields[field_name].type != "boolean"
                ):
                    site_value = None

                # Add the data to the values
                values.append(
                    {"onlogic_company": company.short_name.upper(), "value": site_value}
                )
            except AccessError:
                # Some records are restricted to a single company
                _logger.debug(
                    "GraphQL warning. Access is not permitted for field [%s.%s %s], company [%s]",
                    record._name,
                    field_name,
                    record.id,
                    company.short_name,
                )
            except AttributeError as exc:
                raise ValidationError(
                    f"GraphQL error. `{base_record}{f'.{relations}' if relations else ''}` does not not have"
                    f" field `{field_name}` defined!"
                ) from exc
            except KeyError as exc:
                raise ValidationError(
                    f"GraphQL error. Invalid relation `{relations}` for record `{base_record._name}`"
                ) from exc
        return values

    @staticmethod
    def resolve_graphql_successful(odoo_record, _):
        """
        TODO: Build out this feature better, so we can give more precise reporting on the results of the mutation

        The only way I can see that we could do this is by returning graphql successful for the initial call, subscription or graphiql mutation but then for subsequent calls after the mutation is done then we can return more detail. This doesn't necessarily seem like it would give a large benefit for adding more complexity
        """

        if "graphql_successful" in odoo_record.env.context:
            return odoo_record.env.context["graphql_successful"]

        return True

    @staticmethod
    def resolve_odoo_url(odoo_record, _):
        return odoo_record.get_url()

    @staticmethod
    def resolve_date_data(odoo_record, _):
        """
        Get a dictionary of dates when the given record was updated or modified by Odoo
        """
        date_data = odoo_record.get_record_dates_data()
        date_data = {k: str(v) for k, v in date_data.items()}
        return date_data
