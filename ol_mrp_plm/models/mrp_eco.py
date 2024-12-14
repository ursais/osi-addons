# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MRPEco(models.Model):
    """
    Inherit MRP Eco for Method Overriding.
    """

    _inherit = "mrp.eco"

    # COLUMNS ##########

    company_id = fields.Many2one("res.company", string="Company", default=False)

    # END ##############
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
        # Check if the stage_id is being updated
        if "stage_id" in vals:
            stage = self.env["mrp.eco.stage"].browse(vals["stage_id"])
            for eco in self:
                # Check if final_stage is True
                if stage.final_stage:

                    product_template = eco.product_tmpl_id
                    # Validate if product_tmpl_id is not purchase_ok and has no vendor pricelist
                    if product_template.purchase_ok and not product_template.seller_ids:
                        raise UserError(
                            _(
                                "The product associated with this ECO does not have a"
                                " vendor pricelist defined. Please add a vendor"
                                " pricelist to the product before moving this ECO to"
                                " the final stage."
                            )
                        )
        res = super().write(vals)
        if (
            vals.get("stage_id", False)
            and self.product_tmpl_id
            and self.stage_id.product_state_id
        ):
            self.product_tmpl_id.product_state_id = self.stage_id.product_state_id.id
        return res

    # END #########
