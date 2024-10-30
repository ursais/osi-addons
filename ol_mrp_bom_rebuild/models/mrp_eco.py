# Import Odoo libs
from odoo import api, models


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

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl_id(self):
        """
        When product_tmpl_id is changed, this method checks if there are
        existing BoMs associated with the product template:
            - If any BoM has the scaffolding_bom flag, it sets self.bom_id to that BoM.
            - If no scaffolding_bom is found but there is a BoM without a specific
              product (product_id not set), it assigns the first such BoM to
              self.bom_id.
            - If neither condition is met, it falls back to the default behavior
              of onchange_product_tmpl_id using super()
        """
        bom_ids = self.product_tmpl_id.bom_ids
        if bom_ids and bom_ids.filtered(lambda l: l.scaffolding_bom):
            self.bom_id = bom_ids.filtered(lambda l: l.scaffolding_bom).id
        elif bom_ids and bom_ids.filtered(lambda l: not l.product_id):
            self.bom_id = bom_ids.filtered(lambda l: not l.product_id).ids[0]
        else:
            super().onchange_product_tmpl_id()

    # END #########
