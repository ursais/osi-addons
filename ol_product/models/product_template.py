# Import Odoo Libs
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    """
    Add length,width and height to ProductTemplate
    """

    # METHODS #####

    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")

    # END #########
