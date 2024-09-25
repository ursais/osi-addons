# Import Odoo libs
from odoo import api,models


class MRPEco(models.Model):
    """
    Inherit MRP Eco to rebuild Variant BoM's when apply change button is pressed.
    """

    _inherit = "mrp.eco"

    # METHODS #####

    def action_apply(self):
        """
        When apply changes button is applied, then update variant BoM's
        from scaffolding BoM. This method only makes new BoM versions if
        differences are found.
        """
        result = super(MRPEco, self).action_apply()
        for eco in self:
            if eco.type == "bom":
                eco.product_tmpl_id._reset_all_variants_bom_with_scaffold_bom()
        return result

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl_id(self):
        bom_ids = self.product_tmpl_id.bom_ids
        if bom_ids and bom_ids.filtered(lambda l:l.scaffolding_bom):
            self.bom_id = bom_ids.filtered(lambda l:l.scaffolding_bom).id
        elif bom_ids and bom_ids.filtered(lambda l:not l.product_id):
            self.bom_id = bom_ids.filtered(lambda l:not l.product_id).ids[0]
        else:
            super().onchange_product_tmpl_id()
    # END #########
