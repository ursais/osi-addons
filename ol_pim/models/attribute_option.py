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

    # Commenting this out until there is confirmation that these should be unique
    # @api.constrains("code")
    # def _check_unique_code(self):
    #     for record in self:
    #         existing_record = self.search([("code", "=", record.code)], limit=1)
    #         if existing_record and existing_record.id != record.id:
    #             raise ValidationError(
    #                 f"The Attribute Option Code '{record.code}' must be unique. Please choose a different code."
    #             )
