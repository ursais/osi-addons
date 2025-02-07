# Import Odoo Libs
from odoo import fields, models


class ProductAttributeClassification(models.Model):
    """
    Classification of product attributes
    """

    _name = "product.attribute.classification"
    _description = "Classification of an attribute (Motherboard, Memory, Case, etc)"

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Option Title must be unique!"),
    ]

    # COLUMNS #####

    name = fields.Char(string="Classification Name")

    # END #########
