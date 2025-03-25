# Import Odoo libs
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    Add warranty period product template.
    """

    _inherit = "product.template"

    # COLUMNS ###

    warranty_period = fields.Selection(
        [
            ("1", "1 Year"),
            ("2", "2 Years"),
            ("3", "3 Years"),
            ("4", "4 Years"),
            ("5", "5 Years"),
            ("6", "6 Years"),
            ("7", "7 Years"),
            ("8", "8 Years"),
            ("9", "9 Years"),
            ("10", "10 Years"),
        ],
        string="Warranty Period",
        help="Defines the warranty period in years to be set on serial numbers.",
    )

    # END #######
