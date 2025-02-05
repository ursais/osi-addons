# Import Odoo libs
from odoo import fields, models


class AttributeGroup(models.Model):
    """
    Adding fields to Attribute Group.
    """

    _inherit = "attribute.group"

    # COLUMNS ##########

    code = fields.Char(
        string="Code",
    )

    # END ##########
