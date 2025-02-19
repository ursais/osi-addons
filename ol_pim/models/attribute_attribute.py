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
        required=True,
    )

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            "The Attribute Code must be unique. Please choose a different code.",
        )
    ]
    # END ##########
