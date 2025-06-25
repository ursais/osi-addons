# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType
from odoo.addons.ol_graphql_user.schema.res_user.interface import (
    UserInterface,
)
from odoo.addons.ol_graphql_partner.schema.res_partner.types import Partner


class User(OnLogicBaseObjectType, UserInterface):
    """
    Graphene type for `res.users` records
    """

    id = graphene.Int()
    login = graphene.String()
    company_id = graphene.Int()
    active = graphene.Boolean()
    partner_id = graphene.Field(lambda: Partner)
    name = graphene.String()
