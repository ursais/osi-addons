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

    def _set_visibility_based_on_sale_description(self):
        # Utility method to set visibility based on 'used_in_sale_description'
        visible = self.used_in_sale_description
        self.product_template_value_ids.write({"visible_to_user": visible})

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        for line in results:
            line._set_visibility_based_on_sale_description()
        return results

    def write(self, values):
        results = super().write(values)
        # Apply changes only if 'used_in_sale_description' has been modified
        if "used_in_sale_description" in values:
            self._set_visibility_based_on_sale_description()
        return results

    # END #########
