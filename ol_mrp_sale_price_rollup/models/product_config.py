# Import Odoo libs
from odoo import api, models


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def create_get_variant(self, value_ids=None, custom_vals=None):
        """Inherit the method to set the sales price from
        bom when configured/created."""
        variant = super().create_get_variant(
            value_ids=value_ids,
            custom_vals=custom_vals,
        )
        additional_total = variant._get_bom_sale_price()
        variant.lst_price = additional_total
        return variant

    @api.depends(
        "value_ids",
        "product_id.lst_price",  # Change to variant lst_price
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.attribute_line_ids.value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids.price_extra",
    )
    def _compute_cfg_price(self):
        # Call super to preserve original functionality
        super()._compute_cfg_price()

        # Now extend the functionality to use variant price
        for session in self:
            if session.product_id:  # Using product variant instead of template
                # Recalculate price based on variant's lst_price using your custom logic
                price = session.with_company(session.company_id).get_cfg_price()
                session.price = price

    @api.model
    def get_cfg_price(self, value_ids=[], custom_vals=None):
        # Call the original method with super() to preserve its logic
        super().get_cfg_price(value_ids, custom_vals)

        # Now modify the logic to use the variant lst_price instead of the product template
        product_variant = self.product_id  # Assuming this refers to the variant
        value_ids = value_ids + self.value_ids.ids

        # You can adjust any context or additional logic here if needed
        if self.env.context.get("tobe_remove_attr", []):
            value_ids = self.flatten_val_ids(value_ids)
            value_ids = set(value_ids) - set(
                self.env.context.get("tobe_remove_attr", [])
            )
            value_ids = list(value_ids)

        value_ids = self.flatten_val_ids(value_ids)

        # Return price using variant's lst_price instead of template list_price
        return product_variant.lst_price
