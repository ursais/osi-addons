# Import Odoo Libs
from odoo.addons.ol_graphql.schema.query import BaseQuery
from odoo.addons.ol_graphql_partner.schema.res_partner.types import Partner


class Query(BaseQuery):
    """
    The Root query for partners requests
    """

    partners = BaseQuery.get_base_query(Partner)

    @classmethod
    def resolve_partners(cls, parent, info, **kwargs):
        return cls.base_resolver(info=info, odoo_class="res.partner", args=kwargs)
