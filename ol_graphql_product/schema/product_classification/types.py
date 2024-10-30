# Import Python Libs
import graphene

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import OnLogicBaseObjectType


class ProductClassification(OnLogicBaseObjectType):
    """
    Graphene type for `product.attribute.classification` records
    """

    id = graphene.Int()
    name = graphene.String()
    assembly_stage = graphene.String()

    @staticmethod
    def resolve_assembly_stage(record, _):
        return record.stage_id.name if record.stage_id else None
