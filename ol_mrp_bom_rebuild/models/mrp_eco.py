from odoo import models


class MRPEco(models.Model):
    _inherit = "mrp.eco"

    def action_apply(self):
        for eco in self:
            if eco.allow_apply_change and eco.type == 'product':
                eco.product_tmpl_id._reset_all_variants_bom_with_master_bom()
        return super(MRPEco, self).action_apply()
