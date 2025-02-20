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
        required=True,
    )

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            "The Attribute Set Code must be unique. Please choose a different code.",
        )
    ]

    # END ##########
