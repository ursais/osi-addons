# Import Odoo libs
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
        selection_add=[
            ("nullable_integer", "Nullable Integer"),
            ("nullable_float", "Nullable Float"),
        ],
        ondelete={
            "nullable_integer": "set integer",
            "nullable_float": "set float",
        },
    )

    # END ##########
    # CONSTRAINTS ##########

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            "The Attribute Code must be unique. Please choose a different code.",
        )
    ]

    @api.constrains("attribute_type", "model_id")
    def _check_attribute_type_for_products(self):
        """Prevent product.template and product.product from using non-nullable integer/float types."""
        for rec in self:
            if (
                rec.model_id
                and rec.model_id.model in ["product.template", "product.product"]
                and rec.attribute_type in ["integer", "float"]
            ):
                raise ValidationError(
                    _(
                        "Attributes of type 'Integer' or 'Float' are not allowed "
                        "for product templates or variants.\n"
                        "Please use 'Nullable Integer' or 'Nullable Float' instead."
                    )
                )

    # END ##########
