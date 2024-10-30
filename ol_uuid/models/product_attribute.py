# Import Odoo libs
from odoo import models


class ProductAttribute(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'product.attribute'
    _inherit = ['product.attribute', 'res.uuid']
