# Import Python Libs
import logging
import graphene
from graphql import GraphQLError
from odoo.exceptions import AccessDenied
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class BaseQuery(graphene.ObjectType):
    """
    The base GraphQL query resolver
    """

    def base_resolver(info, odoo_class, args):
        """
        The resolve function used by default
        """

        env = info.context["env"]

        if not env.context.get(
            "graphql_api_client_signature_validated", False
        ) and not env.user.user_has_groups("ol_graphql.graphql_query"):
            _logger.warning(
                f"GraphQL Error: Access denied! User `{env.user.name} ({env.user})"
                " has no permission to run GraphQL Queries!"
            )
            raise AccessDenied()

        transaction_id = args.get("transaction_id", False)
        # Set up the domain and search limit based on the received `uuid` or `uuids`
        domain = []
        limit = args.get("limit", False)
        offset = args.get("offset", False)
        order = args.get("order", False)
        uuid = args.get("uuid", False)
        uuids = args.get("uuids", False)
        updated_since = args.get("updated_since", False)

        if uuid:
            # If the UUID is set that takes priority, we don't need to worry about the rest
            limit = 1
            # No offset should be used if we received a specific UUID
            offset = False
            domain.append(("uuid", "=", uuid))
        elif uuids:
            uuid_len = len(uuids)
            if uuid_len == 1:
                # If UUIDs was defined but we only got one value, we only need to search for that one UUID
                limit = 1
                domain.append(("uuid", "=", uuids[0]))
            else:
                # No limit is needed if we received multiple UUIDs
                limit = None
                domain.append(("uuid", "in", uuids))
            # No offset should be used if we received specific UUIDs
            offset = False
        elif updated_since:
            if hasattr(env[odoo_class], "_get_graphql_updated_since_domain"):
                # Use the odoo model's own domain function
                domain = getattr(env[odoo_class], "_get_graphql_updated_since_domain")(
                    domain, updated_since
                )
            else:
                # Or fall back to the default one
                domain = expression.AND(
                    [[("graphql_update_date", ">=", updated_since)], domain]
                )
        elif not limit:
            raise GraphQLError(
                f"GraphQL Error: Wrong query for`{odoo_class}`. You need to set at least one of these"
                f" query attributes: `uuid`, `uuids`, `updated_since`, `limit` on the query | TI: `{transaction_id}`"
            )

        if offset and not order:
            # If we need to offset the data and the user did not provide an order
            # we should make sure we order the data the same by using the indexed `id`
            order = "id"

        odoo_records = (
            env[odoo_class]
            .sudo()
            .with_context(active_test=False, transaction_id=transaction_id)
            .search(domain, limit=limit, offset=offset, order=order)
        )
        # We switch the found records environment to only active access records!
        odoo_records = odoo_records.with_context(
            active_test=True, transaction_id=transaction_id
        )

        # IMPORTANT:    Instead of an Odoo Record-set we collect the result into a simple array
        #               This necessary as we want to have a different environment owned by the correct company user for each record.
        #               This would not be possible within one Odoo record-set.
        #               Luckily GraphQL handles this array correctly as it can be iterated similarly as a record-set
        company_specific_records = []

        if hasattr(odoo_records, "company_id") or hasattr(odoo_records, "company_ids"):
            # If this Odoo Class has a company field
            for odoo_record in odoo_records:
                # Loop trough each found record

                # Get the record company based on if the record uses `company_id` or `company_ids`
                odoo_record_company = env["res.company"]
                if (
                    hasattr(odoo_record, "company_ids")
                    and len(odoo_record.company_ids) == 1
                ):
                    # If the record could be linked to multiple companies but only one is set we need to use that one
                    odoo_record_company = odoo_record.company_ids
                elif hasattr(odoo_record, "company_id"):
                    odoo_record_company = odoo_record.company_id

                if odoo_record_company:
                    # If the given record's company_id field is set,
                    # make sure we read the record values from that company's "view point"
                    # This is important as certain functions and computed field could return different values based on which company we use
                    company_specific_records.append(
                        odoo_record.with_user(odoo_record_company.company_user_id)
                        .with_company(odoo_record_company.id)
                        .with_context(transaction_id=transaction_id)
                    )
                else:
                    company_specific_records.append(odoo_record)
            # Once done re-assign the original variable
            odoo_records = company_specific_records

        if not odoo_records:
            if updated_since:
                # If no records were found
                # and the query specified a date time (updated_since) that was used to filter which records to return
                # we don't want to throw an error, but rather return an empty recordset!
                return env[odoo_class]
            raise GraphQLError(
                f"GraphQL Error: `{odoo_class}` does not exist in Odoo. Domain: `{domain}`."
                f" Limit: `{limit}` Offset: `{offset}` Order: `{order}` TI: `{transaction_id}`"
            )

        _logger.info(
            f"GraphQL Query: For {odoo_class} | Found {len(odoo_records)} | TI: {transaction_id}"
        )

        # Make sure to add the transaction id
        return odoo_records

    @staticmethod
    def get_base_query(object_type):
        """
        Base definition for all Queries
        """
        return graphene.List(
            graphene.NonNull(object_type),
            required=True,
            order=graphene.String(default_value="id DESC"),
            offset=graphene.Int(default_value=0),
            limit=graphene.Int(),
            uuid=graphene.String(),
            uuids=graphene.List(graphene.String),
            updated_since=graphene.DateTime(),
            transaction_id=graphene.ID(required=False),
        )
