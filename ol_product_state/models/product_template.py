# Import Odoo libs
from odoo import fields, models


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
