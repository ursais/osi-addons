# Import Odoo libs
from odoo import api, fields, models


class ProductTemplateAttributeValue(models.Model):
    """
    Inherit the Product Template Attribute Value Object Adding Fields and methods
    """

    _inherit = "product.template.attribute.value"

    # COLUMNS ##########

    product_id = fields.Many2one(
        comodel_name="product.product",
        related="product_attribute_value_id.product_id",
    )
    company_ids = fields.Many2many(
        comodel_name="res.company",
        related="product_attribute_value_id.company_ids",
    )

    visible_to_user = fields.Boolean(
        string="Visible to User",
    )

    # END ##########
    # METHODS ######

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            value_id = vals.get("product_attribute_value_id")
            if value_id:
                value = self.env["product.attribute.value"].browse(value_id)
                vals["visible_to_user"] = value.visible_to_user
        return super().create(vals_list)

    # END ##########
