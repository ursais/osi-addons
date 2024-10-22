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


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    @api.model
    def get_attribute_value_extra_prices(
        self, product_tmpl_id, pt_attr_value_ids, pricelist=None
    ):
        super().get_attribute_value_extra_prices(
            product_tmpl_id, pt_attr_value_ids, pricelist=None
        )
        extra_prices = {}
        if not pricelist:
            pricelist = self.env.user.partner_id.property_product_pricelist

        related_product_av_ids = self.env["product.attribute.value"].search(
            [("id", "in", pt_attr_value_ids.ids), ("product_id", "!=", False)]
        )
        extra_prices = {
            av.id: av.product_id.with_context(
                pricelist=pricelist.id
            )._get_contextual_price()
            for av in related_product_av_ids
        }
        remaining_av_ids = pt_attr_value_ids - related_product_av_ids
        pe_lines = self.env["product.template.attribute.value"].search(
            [
                ("product_attribute_value_id", "in", remaining_av_ids.ids),
                ("product_tmpl_id", "=", product_tmpl_id),
            ]
        )
        for line in pe_lines:
            attr_val_id = line.product_attribute_value_id
            if attr_val_id.id not in extra_prices:
                extra_prices[attr_val_id.id] = 0
            extra_prices[attr_val_id.id] += line.price_extra
        return extra_prices
