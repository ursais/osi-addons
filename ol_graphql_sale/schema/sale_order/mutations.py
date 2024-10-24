# Import Python Libs
import graphene

# Import Odoo libs
from odoo.addons.ol_graphql.schema.mutator import Mutator
from odoo.addons.ol_graphql.schema.interface import BaseInterface
from odoo.addons.ol_graphql_sale.schema.sale_order.types import SaleOrder
from odoo.addons.ol_graphql_sale.schema.sale_order.decoder import SaleOrderDecoder


class SaleOrderInput(graphene.InputObjectType, BaseInterface):
    """
    Data that can be used to update a Sale Order
    """

    # basic fields
    name = graphene.String()


class SaleOrderMutator(Mutator, SaleOrderDecoder):
    """
    Mutator for SaleOrder mutation processing
    """

    def get_fields_to_exclude(self):
        """
        Define a custom list of fields to exclude for sale order
        """
        core_fields_to_exclude = super().get_fields_to_exclude()
        sale_order_fields_to_exclude = []
        return core_fields_to_exclude + sale_order_fields_to_exclude

    def process_create_data(self):
        """
        Data processing related to sale order creation
        """
        return super().process_create_data()

    def process_data(self):
        """
        Process the message data

        The ol_graphql methods for individual operation types (process_create_data, etc.)
        eventually all call process_data, which we're also hooking into here.
        """

        return super().process_data()


class CreateSaleOrder(graphene.Mutation):
    """
    Create a sale.order object
    """

    class Arguments:
        data = SaleOrderInput(required=True)

    Output = SaleOrder

    @classmethod
    def mutate(cls, parent, info, data):
        # Create the new mutator instance
        mutator = SaleOrderMutator(
            info=info, odoo_class="sale.order", data=data, operation="create"
        )
        # Trigger the create process
        return mutator.create()


class Mutation(graphene.ObjectType):
    """
    Sale Order Mutation class
    """

    create_order = CreateSaleOrder.Field()
