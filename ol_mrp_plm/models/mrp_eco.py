# Import Odoo libs
from odoo import api, models


class MRPEco(models.Model):
    """
    Inherit MRP Eco for Method Overriding.
    """

    _inherit = "mrp.eco"

    # METHODS ##########

    @api.model_create_multi
    def create(self, vals_list):
        """During creation, if the eco stage has a product_state_id set,
        then set the product's state to the eco stage's product state."""
        ecos = super().create(vals_list)
        for eco in ecos:
            if eco.product_tmpl_id and eco.stage_id.product_state_id:
                eco.product_tmpl_id.product_state_id = eco.stage_id.product_state_id.id
        return ecos

    def write(self, vals):
        """During edit, if the eco stage is being changed, and the eco stage has a
        product_state_id set, then set the product's state to the the eco stage's
        product state."""
        result = super().write(vals)
        if (
            vals.get("stage_id", False)
            and self.product_tmpl_id
            and self.stage_id.product_state_id
        ):
            self.product_tmpl_id.product_state_id = self.stage_id.product_state_id.id
        return result

    # END #########
