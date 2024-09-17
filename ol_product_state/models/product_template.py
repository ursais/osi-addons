# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Add restrictions to change product states.
    """

    _inherit = "product.template"

    # COLUMNS ###

    has_product_state_change_group = fields.Boolean(
        compute="_compute_has_product_state_change_group"
    )

    # END #######

    def _compute_has_product_state_change_group(self):
        """Similar to the computed has_configurable_attributes field for view
        visibility, this compute method will set the has_product_state_change_group
        which is then used in the view to make the the product states readonly if
        users don't have the security group.
        """
        for rec in self:
            rec.has_product_state_change_group = self.env["res.users"].has_group(
                "ol_product_state.group_product_state_change"
            )

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        results.onchange_categ_id()
        return results

    def write(self, vals):
        """Prevents users without the group_product_state_change security group
        from updating product states via csv import.
        """
        if (
            "product_state_id" in vals
            and self.env.context.get("import_file")
            and not self.user_has_groups("ol_product_state.group_product_state_change")
        ):
            vals.pop("product_state_id")
        return super().write(vals)

    @api.onchange("categ_id")
    def onchange_categ_id(self):
        """
        Updates the candidate fields of each product in self based on
        the values of the corresponding fields in self.categ_id.
        """
        for product in self:
            for field in [
                "candidate_sale",
                "candidate_sale_confirm",
                "candidate_purchase",
                "candidate_manufacture",
                "candidate_component_manufacture",
                "candidate_bom",
                "candidate_ship",
            ]:
                setattr(product, field, getattr(self.categ_id, field))
