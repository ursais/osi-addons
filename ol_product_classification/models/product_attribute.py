# Import Odoo Libs
from odoo import fields, models


class ProductAttribute(models.Model):
    """
    Add classification to attributes
    """

    _inherit = "product.attribute"

    # COLUMNS #####

    classification_id = fields.Many2one(
        string="Classification",
        comodel_name="product.attribute.classification",
    )

    # END #########
