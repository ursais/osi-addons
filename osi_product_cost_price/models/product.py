# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        "Cost",
        company_dependent=True,
        digits="Product Cost Price",
        groups="base.group_user",
        help="Cost used for stock valuation in standard price"
        " and as a first price to set in average/fifo. "
        "Also used as a base price for pricelists. "
        "Expressed in the default unit of measure of the product.",
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price = fields.Float(
        "Cost",
        compute="_compute_standard_price",
        inverse="_inverse_set_standard_price",
        search="_search_standard_price",
        digits="Product Cost Price",
        groups="base.group_user",
        help="Cost used for stock valuation in standard price"
        " and as a first price to set in average/FIFO.",
    )

    @api.depends_context("company")
    @api.depends("product_variant_ids", "product_variant_ids.standard_price")
    def _compute_standard_price(self):
        # Depends on force_company context because standard_price is company_dependent
        # on the product_product
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.standard_price = template.product_variant_ids.standard_price
        for template in self - unique_variants:
            template.standard_price = 0.0

    def _inverse_set_standard_price(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.standard_price = template.standard_price

    def _search_standard_price(self, operator, value):
        products = self.env["product.product"].search(
            [("standard_price", operator, value)], limit=None
        )
        return [("id", "in", products.mapped("product_tmpl_id").ids)]
