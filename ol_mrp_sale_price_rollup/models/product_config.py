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
        variant._compute_product_lst_price()
        self.price = variant.lst_price

        return variant

    @api.depends(
        "value_ids",
        "product_tmpl_id.list_price",
        "product_id",
        "product_id.lst_price",  # Change to variant lst_price
        "product_id.bom_lst_price",
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.attribute_line_ids.value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids.price_extra",
    )
    def _compute_cfg_price(self):
        """Original method used template list price and now we need to use lst_price
        instead due to bom pricing."""
        super()._compute_cfg_price()

        # Now extend the functionality to use variant price instead of tmpl price
        for session in self:
            if session.product_tmpl_id and not session.product_id:
                price = session.with_company(session.company_id).get_cfg_price()
            elif session.product_id:
                price = session.product_id.lst_price
            else:
                price = 0.00
            session.price = price

    def action_confirm(self, product_id=None):
        for session in self:
            if product_id is None:
                product_id = session.create_get_variant()

            # Recompute lst_price from price_extra to verify BoM pricing was computed
            product_id._compute_product_price_extra()

            session.write({"state": "done", "product_id": product_id.id})
        return super().action_confirm(product_id)
