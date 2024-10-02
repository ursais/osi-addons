# Import Odoo libs
from odoo import api, fields, models


class ProductTemplateAttributeLine(models.Model):
    """
    Add new field to Product Template Attribute Line
    """

    _inherit = "product.template.attribute.line"

    # COLUMNS #####

    used_in_sale_description = fields.Boolean(
        string="Show in Sale Description",
    )

    # END #########
    # METHODS #####
    @api.onchange("attribute_id")
    def _onchange_attribute_id(self):
        if self.attribute_id:
            # Set the value from the related product.attribute field
            self.used_in_sale_description = self.attribute_id.used_in_sale_description

    # END #########
