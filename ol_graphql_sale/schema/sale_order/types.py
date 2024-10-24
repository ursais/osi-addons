# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType
from odoo.addons.ol_graphql.schema.interface import BaseInterface


class SaleOrder(OnLogicBaseObjectType, BaseInterface):
    """
    Graphene type for `sale.order` records
    """

    # basic fields
    id = graphene.ID(required=True)
    name = graphene.String(required=True)
