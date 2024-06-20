from odoo import _, api, fields, models
from odoo.tools.sql import drop_index, index_exists

class ProductProductAttributeValueQty(models.Model):
    _name = "product.product.attribute.value.qty"
    _description = "A link between variants and attributes and the quantity of that combination Fields"

    product_id = fields.Many2one("product.product",string="Product Variant",ondelete="cascade")
    attr_value_id = fields.Many2one("product.attribute.value",required=True)
    qty = fields.Integer(string="Quantity")


    @api.depends("attr_value_id", "qty")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for rec in self:
            if rec.attr_value_id and rec.qty:
                rec.display_name = rec.attr_value_id.display_name + "(" + str(rec.qty) +")"
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"
    _rec_name = "config_name"

    @api.depends('product_attribute_value_qty_ids')
    def _compute_qty_combination_indices(self):
        for product in self:
            qty_combination_indices = product.product_attribute_value_qty_ids.mapped('qty')
            product.qty_combination_indices = ','.join([str(i) for i in sorted(qty_combination_indices)])


    product_attribute_value_qty_ids = fields.One2many("product.product.attribute.value.qty","product_id")
    qty_combination_indices = fields.Char(compute='_compute_qty_combination_indices', store=True, index=True)

    def init(self):
        if index_exists(self.env.cr, "product_product_combination_unique"):
            drop_index(self.env.cr, "product_product_combination_unique", self._table)

        self.env.cr.execute("CREATE UNIQUE INDEX IF NOT EXISTS product_product_combination_qty_attrs_unique ON %s (product_tmpl_id, combination_indices,qty_combination_indices) WHERE active is true"
            % self._table)