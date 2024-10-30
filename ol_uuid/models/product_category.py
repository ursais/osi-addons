# Import Odoo libs
from odoo import models


class ProductCategory(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'product.category'
    _inherit = ['product.category', 'res.uuid']
