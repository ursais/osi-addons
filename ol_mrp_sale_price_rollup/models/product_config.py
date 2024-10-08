# Import Odoo libs
from odoo import api, models
from odoo.exceptions import UserError


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
        "product_tmpl_id.list_price",
        "product_id",
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
            if session.product_tmpl_id and not session.product_id:
                price = session.with_company(session.company_id).get_cfg_price()
            elif session.product_id:
                price = session.product_id.lst_price
            else:
                price = 0.00
            session.price = price
