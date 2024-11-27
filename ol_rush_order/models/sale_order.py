from odoo import api,models,fields

class ProductTemplate(models.Model):

    _inherit = 'sale.order'

    rush_order = fields.Boolean("Rush Order")

    @api.onchange('order_line','order_line.product_id')
    def _onchange_rush_order(self):
        self.rush_order = any(product_id.triggers_rush for product_id in self.mapped('order_line').mapped('product_id'))
