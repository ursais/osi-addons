# Import Odoo libs
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # METHODS ##########

    def write(self, vals):
        res = super().write(vals)
        obsolete_state = self.env.ref("product_state.product_state_obsolete", raise_if_not_found=False)
        if 'product_state_id' in vals:
            # Filter for templates being changed to 'obsolete'
            templates_becoming_obsolete = self.filtered(lambda t: obsolete_state and obsolete_state.id == vals.get('product_state_id'))
            # Trigger exception logic only for affected templates
            if templates_becoming_obsolete:
                templates_becoming_obsolete._trigger_exception_rules()
        return res

    def _trigger_exception_rules(self):
        # Find sale orders that include any variant of these templates
        related_sale_orders = self.env['sale.order.line'].search([
            ('product_id.product_tmpl_id', 'in', self.ids)
        ]).mapped('order_id')

        # Efficiently trigger the exception checks
        if related_sale_orders:
            related_sale_orders.sale_check_exception()

        return True

    # END ##########
