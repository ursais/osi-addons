# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType


class ProductTaxCode(OnLogicBaseObjectType):
    """
    Graphene type for `product.tax.code` records
    """

    id = graphene.Int()
    name = graphene.String()
    type = graphene.String()
    description = graphene.String()
