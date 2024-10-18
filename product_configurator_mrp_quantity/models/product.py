from odoo import api, fields, models
from odoo.tools.sql import drop_index, index_exists


class ProductProductAttributeValueQty(models.Model):
    _name = "product.product.attribute.value.qty"
    _description = "A link between variants and attributes and the quantity of that combination Fields"

    product_id = fields.Many2one(
        "product.product", string="Product Variant", ondelete="cascade"
    )
    attr_value_id = fields.Many2one("product.attribute.value", required=True)
    qty = fields.Integer(string="Quantity")
    attribute_value_qty_id = fields.Many2one("attribute.value.qty", ondelete="cascade")

    @api.depends("attr_value_id", "qty")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for rec in self:
            if rec.attr_value_id and rec.qty:
                rec.display_name = (
                    rec.attr_value_id.display_name + "(" + str(rec.qty) + ")"
                )
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"
    _rec_name = "config_name"

    @api.depends("product_attribute_value_qty_ids")
    def _compute_qty_combination_indices(self):
        for product in self:
            qty_combination_indices = product.product_attribute_value_qty_ids.mapped(
                "qty"
            )
            product.qty_combination_indices = ",".join(
                [str(i) for i in qty_combination_indices]
            )

    product_attribute_value_qty_ids = fields.One2many(
        "product.product.attribute.value.qty", "product_id"
    )
    qty_combination_indices = fields.Char(
        compute="_compute_qty_combination_indices", store=True, index=True
    )

    def init(self):
        if index_exists(self.env.cr, "product_product_combination_unique"):
            drop_index(self.env.cr, "product_product_combination_unique", self._table)

        self.env.cr.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS product_product_combination_qty_attrs_unique ON %s (product_tmpl_id, combination_indices,qty_combination_indices) WHERE active is true"
            % self._table
        )

    def _get_non_config_set_bom_lines(self):
        self.ensure_one()
        attribute_value = self.env["product.attribute.value"]
        current_bom = self.env["mrp.bom"]._bom_find(self)[self]
        additional_total = 0
        for bom_line in current_bom.bom_line_ids:
            if bom_line.child_bom_id:
                for child_bom_line in bom_line.child_bom_id.bom_line_ids:
                    additional_total += (
                        child_bom_line.product_id.uom_id._compute_price(
                            child_bom_line.product_id.lst_price,
                            child_bom_line.product_uom_id,
                        )
                        * child_bom_line.product_qty
                    )
            elif not bom_line.child_bom_id:
                additional_total += (
                    bom_line.product_id.uom_id._compute_price(
                        bom_line.product_id.lst_price, bom_line.product_uom_id
                    )
                    * bom_line.product_qty
                )

        return additional_total

    def _get_bom_sale_price(self):
        attribute_value_obj = self.env["product.attribute.value"]
        value_ids = self.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id"
        ).filtered(lambda l: not l.product_id)
        extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
            product_tmpl_id=self.product_tmpl_id.id, pt_attr_value_ids=value_ids
        )
        additional_total = self._get_non_config_set_bom_lines()
        for extra_price in extra_prices:
            additional_qty = self.product_attribute_value_qty_ids.filtered(
                lambda l: l.attr_value_id.id == extra_price
            ).qty
            extra_prices[extra_price] = extra_prices[extra_price] * additional_qty
        return additional_total + sum(extra_prices.values())

    @api.depends("list_price", "price_extra")
    @api.depends_context("uom")
    def _compute_product_lst_price(self):
        rec = super()._compute_product_lst_price()
        for product in self.filtered(lambda l: l.config_ok):
            additional_total = product._get_bom_sale_price()
            product.lst_price = additional_total
        return rec

    def _compute_product_price_extra(self):
        standard_products = self.filtered(lambda product: not product.config_ok)
        config_products = self - standard_products
        if standard_products:
            result = super(
                ProductProduct, standard_products
            )._compute_product_price_extra()
        else:
            result = None
        for product in config_products:
            attribute_value_obj = self.env["product.attribute.value"]
            value_ids = (
                product.product_template_attribute_value_ids.product_attribute_value_id
            )
            extra_prices = attribute_value_obj.get_attribute_value_extra_prices(
                product_tmpl_id=product.product_tmpl_id.id, pt_attr_value_ids=value_ids
            )
            for extra_price in extra_prices:
                matching_records = self.product_attribute_value_qty_ids.filtered(
                    lambda l: l.attr_value_id.id == extra_price
                )
                # Ensure there are records and handle multiple records if necessary
                if matching_records:
                    additional_qty = sum(matching_records.mapped("qty"))
                    extra_prices[extra_price] = (
                        extra_prices[extra_price] * additional_qty
                    )
            product.price_extra = sum(extra_prices.values())
        return result
