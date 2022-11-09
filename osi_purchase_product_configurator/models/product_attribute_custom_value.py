from odoo import fields, models


class ProductAttributeCustomValue(models.Model):
    _inherit = "product.attribute.custom.value"

    purchase_order_line_id = fields.Many2one('purchase.order.line', string="Purchase Order Line", required=True, ondelete='cascade')

    _sql_constraints = [
        ('pol_custom_value_unique', 'unique(custom_product_template_attribute_value_id, purchase_order_line_id)', "Only one Custom Value is allowed per Attribute Value per Purchase Order Line.")
    ]
