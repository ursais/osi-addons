# Import Odoo libs
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """
    Add new fields to Sale Order Line
    """

    _inherit = "sale.order.line"

    # COLUMNS #####

    product_state_id = fields.Many2one(related="product_template_id.product_state_id")

    # END #########
    # METHODS #####

    @api.model_create_multi
    def create(self, vals):
        """
        Override create method to include attribute values in the name
        of the record based on product attribute line settings.
        """
        res = super().create(vals)

        for rec in res:
            # Check if the product has template attribute values
            if rec.product_id.product_template_attribute_value_ids:
                # Start with the product's name as the base description
                description = rec.product_id.name

                for (
                    attribute_value
                ) in rec.product_id.product_template_attribute_value_ids:
                    # Retrieve the attribute line for the current attribute value
                    attribute_line = (
                        rec.product_id.product_tmpl_id.attribute_line_ids.filtered(
                            lambda line: line.attribute_id
                            == attribute_value.attribute_id
                        )
                    )

                    # If 'used_in_sale_description' is True, add attribute to description
                    if attribute_line and attribute_line.used_in_sale_description:
                        description += "\n  " + attribute_value.display_name
                rec.name = description
        return res

    def write(self, vals):
        """
        Override write method to update record's name with attribute values
        based on changes in 'product_id' and attribute line settings.
        """
        res = super().write(vals)

        for rec in self:
            # If 'product_id' is being updated, adjust the record's description
            if vals.get("product_id"):
                # Get the new product record from 'product_id'
                product = rec.env["product.product"].browse(vals["product_id"])

                # Check if the product has template attribute values
                if product.product_template_attribute_value_ids:
                    # Start with the product's name as the base description
                    description = product.name

                    for attribute_value in product.product_template_attribute_value_ids:
                        # Retrieve the attribute line for the current attribute value
                        attribute_line = (
                            product.product_tmpl_id.attribute_line_ids.filtered(
                                lambda line: line.attribute_id
                                == attribute_value.attribute_id
                            )
                        )

                        # If 'used_in_sale_description' is True, add attribute to description
                        if attribute_line and attribute_line.used_in_sale_description:
                            description += "\n  " + attribute_value.display_name
                    rec.name = description
        return res

    # END #########
