# Import Python Libs
import graphene

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
    name = graphene.String()
    position = graphene.Int()
    required = graphene.Boolean()
    selections = graphene.List(ProductConfigurationOption)
    uuid = graphene.ID()
