# Import Python Libs
import graphene
from graphene.types.generic import GenericScalar


class ProductConfigurationOption(graphene.ObjectType):
    """
    Graphene type for product configuration relation options
    There are gather information from multiple Odoo records:
    - `product.template.attribute.line`
    - `product.template.attribute.value`
    - `product.attribute.value`
    - `product.template`
    - `product.product`
    """

    default_qty = graphene.Int()
    is_default = graphene.Boolean()
    enabled = GenericScalar()
    is_user_defined_qty = graphene.Boolean()
    max_qty = graphene.Int()
    uuid = graphene.ID()
    visible_to_user = graphene.Boolean()
    sequence = graphene.Int()
