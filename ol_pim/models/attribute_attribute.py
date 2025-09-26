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

    attribute_type = fields.Selection(
        [
            ("char", "Char"),
            ("text", "Text"),
            ("select", "Select"),
            ("multiselect", "Multiselect"),
            ("boolean", "Boolean"),
            ("nullable_integer", "Integer"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("binary", "Binary"),
            ("nullable_float", "Float"),
        ],
    )

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            "The Attribute Code must be unique. Please choose a different code.",
        )
    ]
    # END ##########
