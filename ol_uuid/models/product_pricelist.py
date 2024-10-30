# Import Odoo libs
from odoo import models, api
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'product.pricelist'
    _inherit = ['product.pricelist', 'res.uuid']


class ProductPricelistItem(models.Model):
    """
    Add UUID compatibility
    """

    _name = 'product.pricelist.item'
    _inherit = ['product.pricelist.item', 'res.uuid']
