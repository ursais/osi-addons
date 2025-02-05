# Import Odoo libs
from odoo import fields, models


class AttributeSet(models.Model):
    """
    Adding fields to Attribute Set.
    """

    _inherit = "attribute.set"

    # COLUMNS ##########

    code = fields.Char(
        string="Code",
    )

    # END ##########
