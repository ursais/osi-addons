# Import Odoo Libs
from odoo.addons.ol_graphql.schema.query import BaseQuery
from odoo.addons.ol_graphql_product.schema.product.types import ProductTemplate


class Query(BaseQuery):
    """
    The Root query
    """

    products = BaseQuery.get_base_query(ProductTemplate)

    @classmethod
    def resolve_products(cls, parent, info, **kwargs):
        return cls.base_resolver(info=info, odoo_class="product.template", args=kwargs)
