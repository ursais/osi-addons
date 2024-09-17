# Import Odoo libs
from odoo import models


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

    # END #########
