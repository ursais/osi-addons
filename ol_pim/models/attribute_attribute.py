# Import Odoo libs
from odoo import fields, models


class AttributeAttribute(models.Model):
    """
    Adding fields to Attributes.
    """

    _inherit = "attribute.attribute"

    # COLUMNS ##########

    code = fields.Char(
        string="Code",
    )

    # END ##########
