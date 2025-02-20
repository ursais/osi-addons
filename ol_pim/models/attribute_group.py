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
        required=True,
    )

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            "The Attribute Group Code must be unique. Please choose a different code.",
        )
    ]

    # END ##########
