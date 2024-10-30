# Import Odoo libs
from odoo import models


class PricelistItem(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "product.pricelist.item"
    _inherit = ["product.pricelist.item", "graphql.mixin"]
