# Import Odoo libs
from odoo import api, models


class MRPBOMLine(models.Model):
    _inherit = "mrp.bom.line"

    @api.model_create_multi
    def create(self,vals_list):
        results = super().create(vals_list)
        if results.filtered(lambda l:l.bom_id.type == "phantom"):
            results.mapped("bom_id.product_tmpl_id").button_bom_sale_price()
        return results

    def unlink(self):
        bom_id = self.bom_id
        results = super().unlink()
        if bom_id.type =="phantom":
            bom_id.product_tmpl_id.button_bom_sale_price()
        return results