from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _can_be_added_to_cart(self):
        res = super(ProductTemplate, self)._can_be_added_to_cart()
        if not self._context.get('pricelist'):
            return True
        return res
