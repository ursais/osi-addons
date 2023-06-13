from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_template_id = fields.Many2one('product.template', 'Product', domain=[("purchase_ok", "=", True)])
    is_configurable_product = fields.Boolean('Is the product configurable?', related="product_template_id.has_configurable_attributes")
    product_template_attribute_value_ids = fields.Many2many(related='product_id.product_template_attribute_value_ids', readonly=True)
    product_custom_attribute_value_ids = fields.One2many('product.attribute.custom.value', 'purchase_order_line_id',
                                                         string="Custom Values", copy=True)
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value', string="Extra Values",
                                                              ondelete='restrict')

    @api.onchange('product_id')
    def onchange_product_id(self):
        for po_line in self:
            if not po_line.display_type in ['line_section', 'line_note']:
                qty = self.product_qty or 1
                res = super(PurchaseOrderLine, self).onchange_product_id()
                if self._context.get('default_product_uom_qty'):
                    self.product_qty = self._context.get('default_product_uom_qty')
                else:
                    self.product_qty = qty
                return res
