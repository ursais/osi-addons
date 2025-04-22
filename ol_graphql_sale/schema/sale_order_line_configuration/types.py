# Import Python Libs
import graphene


class SaleOrderLineConfiguration(graphene.ObjectType):
    """
    This represent the Product Configuration options on a Sale Order Line
    """

    sku = graphene.String()
    product = graphene.ID()
    option = graphene.ID()
    qty = graphene.Int()

    @staticmethod
    def resolve_sku(configuration, _):
        ptav, ppavq = configuration
        return ptav.product_attribute_value_id.product_id.default_code or None

    @staticmethod
    def resolve_product(configuration, _):
        ptav, ppavq = configuration
        return ptav.product_attribute_value_id.product_id.uuid or None

    @staticmethod
    def resolve_option(configuration, _):
        ptav, ppavq = configuration
        return ptav.attribute_id.uuid or None

    @staticmethod
    def resolve_qty(configuration, _):
        """
        PPAVQ records are only created if the `is_qty_required` flag is set, so we can assume that if these records don't exist then the quantity is 1
        """
        ptav, ppavq = configuration
        return ppavq.qty or 1
