# Import Odoo Libs
from odoo import fields, models


class MrpBomLine(models.Model):
    """
    Add fields to bom lines
    """

    _inherit = "mrp.bom.line"

    # COLUMNS #####

    classification_id = fields.Many2one(
        string="Classification",
        comodel_name="product.attribute.classification",
        index=True,
    )

    # END #########
