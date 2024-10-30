# Import Odoo libs
from odoo import models


class ProductTaxCode(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'product.tax.code'
    _inherit = ['product.tax.code', 'res.uuid']
