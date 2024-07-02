# Import Odoo libs
from odoo import _, models, exceptions


class MRPBom(models.Model):
    """
    Inherit MRP Bom for Method Overriding.
    """

    _inherit = "mrp.bom"

    # METHODS ##########

    def write(self, vals):
        mrp_eco_stages = self.env["mrp.eco.stage"].search(
            [
                ("product_state_id", "=", self.product_tmpl_id.product_state_id.id),
                ("allow_bom_edits", "=", True),
            ],
            limit=1,
        )
        restricted_fields = [
            "product_tmpl_id",
            "product_id",
            "bom_line_ids",
            "product_qty",
            "bom_line_config_ids",
            "operation_ids",
            "type",
        ]
        if (
            any(field in list(vals.keys()) for field in restricted_fields)
            and not self.user_has_groups("ol_mrp_plm.group_bypass_bom_restiction")
            and not mrp_eco_stages
        ):
            raise exceptions.ValidationError(
                _(
                    "Cannot update '%s' BOM because either there are no active ECO’s "
                    "in a stage that allows editing this BOM."
                    "\nPlease make sure a PLM ECO is in a stage that permits editing.",
                    self.product_tmpl_id.name,
                )
            )
        return super().write(vals)

    # END #########
