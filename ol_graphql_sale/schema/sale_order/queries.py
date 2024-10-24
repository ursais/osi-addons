# Import Odoo Libs
from odoo.addons.ol_graphql.schema.query import BaseQuery
from odoo.addons.ol_graphql_sale.schema.sale_order.types import SaleOrder


class Query(BaseQuery):
    """
    The Root query
    """

    sale_orders = BaseQuery.get_base_query(SaleOrder)

    @classmethod
    def resolve_sale_orders(cls, parent, info, **kwargs):
        return cls.base_resolver(info=info, odoo_class="sale.order", args=kwargs)
