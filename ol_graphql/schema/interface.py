# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.logger import GraphQLLogger


class BaseInterface(GraphQLLogger):
    """
    Base interface field definitions etc.
    """

    active = graphene.Boolean()
    uuid = graphene.ID(required=False)
    transaction_id = graphene.ID(required=False)
    origin_system = graphene.String(required=False)
    ordering_key = graphene.ID(required=False)
    odoo_url = graphene.String(required=False)
    message_source = graphene.String(required=False)
    message_publish_time = graphene.String(required=False)
    graphql_successful = graphene.Boolean(required=False)
    graphql_update_date = graphene.DateTime(required=False)
