import graphene

from odoo.addons.ol_graphql.schema.interface import BaseInterface


class EcommerceOrderProcessingErrorInput(graphene.InputObjectType, BaseInterface):
    """
    Graphene type for `ecommerce_order_processing` records
    """

    code = graphene.String()
    message = graphene.String()


class EcommerceOrderProcessingInput(graphene.InputObjectType, BaseInterface):
    """
    Graphene type for `ecommerce_order_processing` records
    """

    status = graphene.String()
    errors = graphene.List(EcommerceOrderProcessingErrorInput)
