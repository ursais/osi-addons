# Import Odoo Libs
from odoo.addons.ol_graphql.schema.query import BaseQuery
from odoo.addons.ol_graphql_customer.schema.res_partner.types import Customer


class Query(BaseQuery):
    """
    The Root query for customers requests
    """

    customers = BaseQuery.get_base_query(Customer)

    @classmethod
    def resolve_customers(cls, parent, info, **kwargs):
        return cls.base_resolver(info=info, odoo_class="res.partner", args=kwargs)
