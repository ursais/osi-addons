# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import ValidationError


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

    # END ##########

    @api.constrains("code")
    def _check_unique_code(self):
        for record in self:
            existing_record = self.search([("code", "=", record.code)], limit=1)
            if existing_record and existing_record.id != record.id:
                raise ValidationError("The code must be unique.")
