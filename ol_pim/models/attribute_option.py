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
        required=True,
    )

    _sql_constraints = [
        (
            "unique_code_per_attribute",
            "UNIQUE(code, attribute_id)",
            """The Attribute Option Code must be unique for each Attribute.
             Please choose a different code.""",
        )
    ]
    # END ##########
