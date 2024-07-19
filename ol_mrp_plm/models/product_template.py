# Import Odoo libs
from odoo import _, models, exceptions


class ProductTemplate(models.Model):
    """
    Inherit Product Template for Method Overriding.
    """

    _inherit = "product.template"

    # METHODS ##########

    def write(self, vals):
        """Restricts certain fields on the BoM so only users with the
        group_bypass_bom_restiction security group can edit those fields.
        This will apply to csv imports also."""
        # Define restricted fields and check if any are being updated
        restricted_fields = [
            "detailed_type",
            "invoice_policy",
            "uom_id",
            "uom_po_id",
            "categ_id",
            "attribute_line_ids",
        ]

        # If any restricted field is being changed and user does not have
        # permissions, raise error.
        if any(
            field in list(vals.keys()) for field in restricted_fields
        ) and not self.user_has_groups("ol_mrp_plm.group_bypass_bom_restiction"):
            open_mrp_ecos = self.env["mrp.eco"].search(
                [
                    ("product_tmpl_id", "=", self.id),
                    ("stage_id.final_stage", "=", False),
                    ("stage_id.allow_bom_edits", "=", True),
                ],
                limit=1,
            )
            if not open_mrp_ecos:
                raise exceptions.ValidationError(
                    _(
                        "Cannot update '%s' Product because either there are no "
                        "active ECO’s in a stage that allows editing this Product."
                        "\nPlease make sure a PLM ECO is in a stage that permits "
                        "editing.",
                        self.name,
                    )
                )
        return super().write(vals)

    # END #########
