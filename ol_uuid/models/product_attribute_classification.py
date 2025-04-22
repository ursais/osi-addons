# Import Odoo libs
from odoo import models


class ProductAttributeClassification(models.Model):
    """
    Add UUID compatibility
    """

    _name = "product.attribute.classification"
    _inherit = ["product.attribute.classification", "res.uuid"]
