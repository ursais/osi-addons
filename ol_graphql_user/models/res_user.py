# Import Odoo libs
from odoo import models


class ResUser(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "res.users"
    _inherit = ["res.users", "graphql.mixin"]
