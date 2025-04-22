# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType

from odoo.addons.ol_graphql_product.schema.product_classification.types import (
    ProductClassification,
)


class ProductAttribute(OnLogicBaseObjectType):
    """
    Graphene type for `product.attribute` records
    """

    id = graphene.Int()
    name = graphene.String()
    display_type = graphene.String()
    classification = graphene.Field(ProductClassification)

    @staticmethod
    def resolve_classification(record, _):
        return record.classification_id or None
