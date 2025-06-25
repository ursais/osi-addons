# Import Python Libs
import graphene
from graphene.types.generic import GenericScalar

# Import Odoo libs
from odoo.addons.ol_graphql.schema.mutator import Mutator
from odoo.addons.ol_graphql.schema.interface import BaseInterface
from odoo.addons.ol_graphql_sale.schema.sale_order.types import SaleOrder
from odoo.addons.ol_graphql_sale.schema.sale_order_line.mutations import (
    SaleOrderLineInput,
)
from odoo.addons.ol_graphql_sale.schema.sale_order.decoder import SaleOrderDecoder
from odoo.addons.ol_graphql_sale.schema.res_partner.decoder import ResPartnerDecoder
from odoo.addons.ol_graphql_partner.schema.res_partner.mutations import PartnerInput
from odoo.addons.ol_graphql.schema.type import CompanyEnumType
from odoo.addons.ol_graphql_sale.schema.ecommerce_order_processing.mutations import (
    EcommerceOrderProcessingInput,
)


class SaleOrderInput(graphene.InputObjectType, BaseInterface):
    """
    Data that can be used to update a Sale Order
    """

    # accept_language = graphene.String() # TODO: waiting for OSI
    account_manager = graphene.Field(lambda: PartnerInput)
    amount_tax = graphene.Float()
    amount_total = graphene.Float()
    billing_address = graphene.Field(lambda: PartnerInput)
    # consumer_type = graphene.String() # TODO: waiting for OSI
    # coupon_code = graphene.String() # TODO: is this ever ingested into odoo?
    customer_group = graphene.ID()
    # customer_ip = graphene.String() # TODO: waiting for OSI
    ecommerce_order_processing = graphene.Field(lambda: EcommerceOrderProcessingInput)
    is_guest = graphene.Boolean()
    locale = graphene.String()
    name = graphene.String()
    onlogic_company = graphene.Field(lambda: CompanyEnumType, required=True)
    order_line = graphene.List(SaleOrderLineInput)
    partner_id = graphene.Field(lambda: PartnerInput)
    # payment_method = GenericScalar() # TODO: waiting for business input
    po_number = graphene.String()
    shipping_address = graphene.Field(lambda: PartnerInput)
    shipping_method = GenericScalar()
    state = graphene.String()
    tax_exemption_code = graphene.String()
    tax_exemption_number = graphene.String()
    # user_agent = graphene.String() # TODO: waiting for OSI

    # IGNORED FIELDS
    amount_untaxed = graphene.Float()
    commercial_partner_id = graphene.Field(lambda: PartnerInput)
    create_date = graphene.String()
    is_quote = graphene.Boolean()
    user_id = graphene.Field(lambda: PartnerInput)


class SaleOrderMutator(Mutator, SaleOrderDecoder, ResPartnerDecoder):
    """
    Mutator for SaleOrder mutation processing
    """

    def get_fields_to_exclude(self):
        """
        Define a custom list of fields to exclude for sale order
        """
        core_fields_to_exclude = super().get_fields_to_exclude()
        sale_order_fields_to_exclude = [
            "amount_untaxed",
            "commercial_partner_id",
            "create_date",
            "is_quote",
            "odoo_url",
            "ordering_key",
            "user_id",
        ]
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
        self.decode_partner_and_addresses()
        # TODO: In odoo 13 we force decode the shipping method here. I don't think this is necessary since we handle order line decoding in a post graphql action, but should double check.
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
