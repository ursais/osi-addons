# Import Python Libs
import graphene

from odoo.addons.ol_graphql_sale.schema.sale_order_line_configuration.mutations import (
    SaleOrderLineConfigurationInput,
)


class SaleOrderLineInput(graphene.InputObjectType):
    """
    Sale Order Line mutation schema.
    """

    configuration = graphene.List(SaleOrderLineConfigurationInput)
    price_unit = graphene.Float()
    product_id = graphene.ID()
    qty = graphene.Int()
    uuid = graphene.ID()
    price_tax = graphene.Float()
    tax_rate = graphene.Float()
