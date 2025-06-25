# Import Python Libs
import graphene
from graphene.types.generic import GenericScalar

# Import Odoo Libs
from odoo.addons.ol_graphql_product.schema.product_configuration_option.types import (
    ProductConfigurationOption,
)


class ProductConfigurationRelation(graphene.ObjectType):
    """
    Graphene type for product configuration relation
    There are gather information from multiple Odoo records:
    - `product.template.attribute.line`
    - `product.attribute.classification`
    - `product.attribute`
    - `product.template`
    """

    classification = graphene.ID()
    classification_name = GenericScalar()
    name = GenericScalar()
    sequence = graphene.Int()
    required = graphene.Boolean()
    selections = graphene.List(ProductConfigurationOption)
    uuid = graphene.ID()
