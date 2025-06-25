# Import Python Libs
import graphene
import logging
from odoo.addons.ol_graphql_sale.schema.sale_order_line_configuration.types import (
    SaleOrderLineConfiguration,
)

_logger = logging.getLogger(__name__)


class SaleOrderLine(graphene.ObjectType):
    """
    Graphene type for `sale.order.line`
    """

    configuration = graphene.List(SaleOrderLineConfiguration)
    price_unit = graphene.Float()
    product_id = graphene.ID()
    qty = graphene.Int()
    uuid = graphene.ID()
    price_tax = graphene.Float()
    tax_rate = graphene.Float()

    @staticmethod
    def resolve_configuration(order_line, _):
        """
        Build a list of configuration tuples that contain product.template.attribute.value records matched with
        the associated product.product.attribute.value.qty record (if there is one)
        """
        return order_line.get_configuration_ptav_ppavq_tuples()

    @staticmethod
    def resolve_tax_rate(order_line, _):
        tax_rate = order_line.tax_id[0].amount if order_line.tax_id else None
        # This is very unusual, but has occurred (see SO with ID 214370 for an example)
        if len(order_line.tax_id) > 1:
            # note: this won't be displayed in service, but we should keep evidence of it in Odoo logs
            _logger.warning(
                f"GraphQL Warning: sale order line with ID {order_line.id} has more than one tax_id"
                f" assigned to it! Tax Ids: {order_line.tax_id}"
            )
            # all prior evidence of multiple account.tax IDs are pairs, one with an amount and one without
            for id in order_line.tax_id:
                if id.amount > 0:
                    tax_rate = id.amount

        return tax_rate

    @staticmethod
    def resolve_qty(order_line, _):
        return order_line.product_uom_qty or None

    @staticmethod
    def resolve_product_id(order_line, _):
        return order_line.product_id.uuid or None
