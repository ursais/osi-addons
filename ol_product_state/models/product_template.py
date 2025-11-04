# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Add restrictions to change product states.
    """

    _inherit = "product.template"

    # COLUMNS ###

    has_product_state_change_group = fields.Boolean(
        compute="_compute_has_product_state_change_group",
    )
    product_state_manually_set = fields.Boolean(
        string="Product State Manually Set",
        default=False,
        help="Indicates that the product state was manually set by a user and should not be automatically reset by system processes.",
        tracking=True,
    )

    # END #######
    # METHODS ###

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

    def _is_system_operation(self):
        """
        Check if the current operation is being performed by the system
        (OdooBot or automated process) rather than by a real user.
        
        Returns True if this is a system operation, False if it's a user operation.
        """
        # Check for context flags that explicitly indicate system operation
        if self.env.context.get("skip_product_state_protection"):
            return False  # Explicitly allow this operation
        if self.env.context.get("from_system_update") or self.env.context.get("from_automation"):
            return True
        
        # Check if user is OdooBot or system user
        # Common system user login patterns in Odoo
        user_login = self.env.user.login or ""
        if user_login.upper() in ("ODOOBOT", "__SYSTEM__", "SYSTEM"):
            return True
        
        # Check if user doesn't have a proper login (system context)
        if not user_login or user_login.startswith("__"):
            return True
        
        return False

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        # Call category onchange to update the candidate fields based on category
        # during creation.
        res.onchange_categ_id()
        return res

    def write(self, vals):
        """
        Prevents users without the group_product_state_change security group
        from updating product states via csv import.
        Also tracks when product state is manually set by users and prevents
        automatic system resets of manually set states.
        """
        # Track manual product state changes by users (not system)
        if "product_state_id" in vals:
            is_system = self._is_system_operation()
            
            if not is_system:
                # User is manually changing the product state
                # Set the flag to protect it from automatic resets
                vals["product_state_manually_set"] = True
            else:
                # System is trying to change the state
                # Check if state was manually set and prevent the change
                manually_set_records = self.filtered(lambda r: r.product_state_manually_set)
                if manually_set_records:
                    # For manually set records, prevent the automatic state change
                    # Remove product_state_id from vals for protected records
                    protected_vals = vals.copy()
                    protected_vals.pop("product_state_id", None)
                    
                    # Write other fields to protected records (if any)
                    if protected_vals:
                        super(ProductTemplate, manually_set_records).write(protected_vals)
                    
                    # Write to non-protected records with original vals (including state change)
                    non_protected = self - manually_set_records
                    if non_protected:
                        result = super(ProductTemplate, non_protected).write(vals)
                    else:
                        result = True
                    return result

        # Prevent users without the group from updating product states via csv import
        if (
            "product_state_id" in vals
            and self.env.context.get("import_file")
            and not self.user_has_groups("ol_product_state.group_product_state_change")
        ):
            vals.pop("product_state_id")
            if "product_state_manually_set" in vals:
                vals.pop("product_state_manually_set")

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

    def toggle_product_state(self):
        """Toggle the product state between 'New/Development'."""
        new_state = self.env.ref(
            "ol_product_state.product_state_new", raise_if_not_found=False
        )
        dev_state = self.env.ref(
            "product_state.product_state_draft", raise_if_not_found=False
        )

        for rec in self:
            if new_state and dev_state:
                if rec.product_state_id == new_state:
                    rec.sudo().write({"product_state_id": dev_state.id, "product_state_manually_set": True})
                elif rec.product_state_id == dev_state:
                    rec.sudo().write({"product_state_id": new_state.id, "product_state_manually_set": True})

    # END #######
