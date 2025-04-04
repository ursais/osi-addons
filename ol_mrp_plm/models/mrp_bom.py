# Import Odoo libs
from odoo import _, api, models, exceptions


class MRPBom(models.Model):
    """
    Inherit MRP Bom for Method Overriding.
    """

    _inherit = "mrp.bom"

    # METHODS ##########

    def write(self, vals):
        """Restricts certain fields on the BoM so only users with the
        group_bypass_bom_restiction security group can edit those fields.
        This will apply to csv imports also."""
        # Define restricted fields and check if any are being updated
        restricted_fields = [
            "product_tmpl_id",
            "product_id",
            "bom_line_ids",
            "product_qty",
            "bom_line_config_ids",
            "operation_ids",
            "type",
        ]

        # If any restricted field is being changed and user does not have
        # permissions, raise error.
        if any(
            field in list(vals.keys()) for field in restricted_fields
        ) and not self.user_has_groups("ol_mrp_plm.group_bypass_bom_restiction"):
            open_mrp_ecos = self.env["mrp.eco"].search(
                [
                    ("product_tmpl_id", "=", self.product_tmpl_id.id),
                    ("stage_id.final_stage", "=", False),
                    ("stage_id.allow_bom_edits", "=", True),
                ],
                limit=1,
            )
            if not open_mrp_ecos:
                raise exceptions.ValidationError(
                    _(
                        "Cannot update '%s' BOM because either there are no active"
                        " ECO’s in a stage that allows editing this BOM."
                        "\nPlease make sure a PLM ECO is in a stage that permits"
                        " editing.",
                        self.product_tmpl_id.name,
                    )
                )
        return super().write(vals)

    @api.model
    def default_get(self, default_fields):
        """
        Overrides the default_get method to modify default values for record creation.
        This method first retrieves the default values using the superclass's
        default_get method. If the 'company_id' field exists in the default values,
        it sets 'company_id' to False.
        Args:
            default_fields (list): A list of fields for which default values are requested.
        Returns:
            dict: A dictionary containing the default values, with 'company_id' set to False if it was initially present.
        """
        res = super().default_get(default_fields)
        if res.get("company_id"):
            res.update({"company_id": False})
        return res

    # END #########
