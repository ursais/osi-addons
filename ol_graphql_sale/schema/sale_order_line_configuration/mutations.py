# Import Python Libs
import graphene


class SaleOrderLineConfigurationInput(graphene.InputObjectType):
    """
    This represent the Product Configuration options on a Sale Order Line mutation schema.
    """

    product = graphene.ID()
    option = graphene.ID()
    qty = graphene.Int()
