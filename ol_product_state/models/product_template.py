# Import Odoo libs
from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    has_product_state_change_group = fields.Boolean(compute="_compute_has_product_state_change_group")

    def _compute_has_product_state_change_group(self):
        for rec in self:
            rec.has_product_state_change_group = self.env["res.users"].has_group(
                "ol_product_state.group_product_state_change"
            )

    def write(self, vals):
        if 'product_state_id' in vals and self.env.context.get('import_file') and not self.user_has_groups('ol_product_state.group_product_state_change'):
            vals.pop('product_state_id')
        return super().write(vals)

