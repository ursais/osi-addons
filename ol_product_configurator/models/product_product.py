# Import Odoo libs
from odoo import api, fields, models


class ProductProduct(models.Model):
    """
    Inherit the Product Variant Object Adding Fields and Methods
    """

    _inherit = "product.product"

    # COLUMNS ##########

    values_company_diff = fields.Boolean(
        default=False,
        copy=False,
        compute="_compute_values_company_diff",
    )

    # END ##########
    # METHODS ##########

    def _compute_values_company_diff(self):
        """Helper method to determine whether to show the banner
        on the product form view."""
        for product in self:
            values_company_diff = False
            for attribute_value in product.product_template_variant_value_ids:
                # Check if company_ids is set and if the user's company is
                # not in company_ids
                if (
                    attribute_value.company_ids
                    and self.env.company.id not in attribute_value.company_ids.ids
                ):
                    values_company_diff = True
                    # No need to continue checking once it's set to True
                    break
            product.values_company_diff = values_company_diff

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        for product in products:
            # Check if the product has a template, has a default code and is configurable
            if product.product_tmpl_id and product.product_tmpl_id.default_code:
                # Generate the new product default code
                if product.product_tmpl_id.config_ok:
                    product.write(
                        {
                            "default_code": f"{product.product_tmpl_id.default_code}-{product.id}"
                        }
                    )
                else:
                    product.write(
                        {"default_code": product.product_tmpl_id.default_code}
                    )
            if product.length and product.weight or product.height:
                product._onchange_volume()
        return products

    def _compute_product_weight(self):
        super()._compute_product_weight()
        for product in self:
            bom = self.env["mrp.bom"]._bom_find(products=product, bom_type="phantom")
            if bom:
                total_weight = 0.0
                bom_id = bom.get(product)
                for line in bom_id.bom_line_ids:
                    total_weight += (line.product_id.weight or 0.0) * line.product_qty
                product.weight = total_weight

    @api.onchange("length", "width", "height")
    def _onchange_volume(self):
        for rec in self:
            rec.volume = (
                (rec.length or 0.0) * (rec.width or 0.0) * (rec.height or 0.0)
            ) / 1000000

    def write(self, vals):
        res = super().write(vals)
        if "length" in vals or "width" in vals or " height" in vals:
            for rec in self:
                rec._onchange_volume()
        return res

    # END ##########
