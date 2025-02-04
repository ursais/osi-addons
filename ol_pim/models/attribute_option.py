# Import Odoo libs
from odoo import fields, models


class AttributeOption(models.Model):
    """
    Adding fields to Attribute Options.
    """

    _inherit = "attribute.option"

    # COLUMNS ##########

    code = fields.Char(
        string="Code",
    )

    # END ##########
