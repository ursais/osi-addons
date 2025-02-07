# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import ValidationError


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

    # END ##########

    @api.constrains("code", "attribute_id")
    def _check_unique_code_per_attribute(self):
        for record in self:
            existing_record = self.search(
                [
                    ("code", "=", record.code),
                    ("attribute_id", "=", record.attribute_id.id),
                ],
                limit=1,
            )
            if existing_record and existing_record.id != record.id:
                raise ValidationError(
                    f"The Attribute Option Code '{record.code}' must be unique for the Attribute '{record.attribute_id.name}'."
                )
