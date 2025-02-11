# Import Odoo libs
from odoo import fields, models


class ProductTemplateAttributeLine(models.Model):
    """
    Inherit the Product Template Attribute Line Object Adding Fields and methods
    """

    _inherit = "product.template.attribute.line"

    # COLUMNS ##########

    visible_to_user = fields.Boolean(string="Visible to User", default=True)

    # END ##########
    # METHODS ##########

    def write(self, vals):
        # Check if 'visible_to_user' is being updated
        if "visible_to_user" in vals:
            visible_to_user = vals["visible_to_user"]
            for template in self:
                # Update visible_to_user for all related product Template attribute value.
                for product in template.product_template_value_ids:
                    product.visible_to_user = visible_to_user
        return super().write(vals)

    # END ##########
