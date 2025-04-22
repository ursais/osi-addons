# Import Odoo Libs
from odoo.addons.ol_graphql.schema.query import BaseQuery
from odoo.addons.ol_graphql_user.schema.res_user.types import User


class Query(BaseQuery):
    """
    The Root query
    """

    users = BaseQuery.get_base_query(User)

    @classmethod
    def resolve_users(cls, parent, info, **kwargs):
        return cls.base_resolver(info=info, odoo_class="res.users", args=kwargs)
