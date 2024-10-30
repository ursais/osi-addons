# Import Python Libs
from collections import defaultdict
import logging
import graphene
from graphene.types.generic import GenericScalar

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.type import UUID
from odoo.addons.ol_graphql.schema.mutator import Mutator
from odoo.addons.ol_graphql_product.schema.product.types import ProductTemplate
from odoo.addons.ol_graphql_product.schema.product.interface import (
    ProductTemplateInterface,
)
from odoo.addons.ol_graphql_product.schema.product.decoder import ProductTemplateDecoder


_logger = logging.getLogger(__name__)


class ProductTemplateInput(graphene.InputObjectType, ProductTemplateInterface):
    """
    Data that can be used to update a product
    """

    image = GenericScalar()


class ProductTemplateMutator(Mutator, ProductTemplateDecoder):
    pass


class UpdateProductTemplate(graphene.Mutation):
    """
    Update a product.template object
    """

    class Arguments:
        uuid = graphene.Argument(UUID, required=True)
        data = ProductTemplateInput(required=True)

    Output = ProductTemplate

    @classmethod
    def mutate(cls, parent, info, uuid, data):
        # Create the new mutator instance
        mutator = ProductTemplateMutator(
            info=info,
            odoo_class="product.template",
            data=data,
            operation="update",
            uuid=uuid,
        )
        # Trigger the update process
        return mutator.update()


class Mutation(graphene.ObjectType):
    """
    ProductTemplate Mutation class
    """

    update_product = UpdateProductTemplate.Field()
