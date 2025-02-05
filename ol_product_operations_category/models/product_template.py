# Import Odoo libs
from odoo import models, fields


class ProductTemplate(models.Model):
    """
    Links Product Templates to Product Operations Categories
    """

    _inherit = "product.template"

    # COLUMNS ##########

    operations_category_id = fields.Many2one(
        string="Operations Category",
        comodel_name="product.operations.category",
        required=False,
        help="Select category for the current product",
    )

    # END ##########
