# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Also adds new triggered field functionality to check exception if a
    triggered field is being updated.
    """

    _inherit = "product.template"

    # COLUMNS ######

    tech_exception = fields.Boolean(string="Tech Exception")

    # END ##########
    # METHODS ######

    def _fields_trigger_check_exception(self):
        # Search for exception configs: sudo is used as non-admins don't
        # have direct access to ir.model
        config_records = (
            self.env["exception.config"]
            .sudo()
            .search([("model_id.model", "=", self._name)])
        )
        fields_to_check = set()
        for config in config_records:
            # Include directly configured fields
            fields_to_check.update(field.name for field in config.trigger_field_ids)
            # Include dynamically discovered related fields
            related_fields = config.get_related_fields()
            fields_to_check.update(field.name for field in related_fields)
        return list(fields_to_check)

    def write(self, vals):
        # --- Track manual state changes to preserve user intent ---
        # Detect if this is a manual state change (not from system/automatic process)
        # Manual changes are those made directly by users, not triggered by exception checks
        # or automatic kit state updates
        is_manual_state_change = False
        if "product_state_id" in vals and not self.env.context.get("skip_kit_state_update", False):
            # Check if this write is from a user action (not automated)
            # If coming from UI or direct user action, preserve the state
            if not self.env.context.get("from_exception_check", False):
                # Check if the new state is "better" (higher sequence) than current
                # This suggests a manual upgrade (e.g., End of Lifecycle -> Active)
                state_model = self.env["product.state"].sudo()
                for product in self:
                    old_state = product.product_state_id
                    new_state = state_model.browse(vals["product_state_id"]) if vals["product_state_id"] else None
                    if old_state and new_state:
                        # If upgrading to a better state, likely manual
                        if new_state.sequence > old_state.sequence:
                            is_manual_state_change = True
                            break
                    elif new_state:
                        # Setting a state where none existed
                        is_manual_state_change = True
                        break
        
        # --- Detect trigger_exception transitions ---
        state_change_triggers = False

        if "product_state_id" in vals:
            state_model = self.env["product.state"].sudo()
            old_product_state_ids = self.mapped("product_state_id").filtered(
                lambda s: s
            )
            new_product_state_id = vals["product_state_id"]
            new_state = (
                state_model.browse(new_product_state_id)
                if new_product_state_id
                else None
            )

            # Compare old and new trigger_exception flags to determine
            # whether to trigger exception checks
            for old_state in old_product_state_ids:
                if old_state.trigger_exception != (
                    new_state.trigger_exception if new_state else False
                ):
                    state_change_triggers = True
                    break

        # --- Detect tech_exception toggle ---
        tech_exception_triggers = False
        if "tech_exception" in vals:
            old_values = self.mapped("tech_exception")
            new_value = vals["tech_exception"]
            # If any record's value differs from the incoming one, trigger
            if any(old != new_value for old in old_values):
                tech_exception_triggers = True

        # Detect relevant field changes that also require downstream checks
        trigger_fields = self._fields_trigger_check_exception()
        relevant_changes = {
            field: vals[field] for field in trigger_fields if field in vals
        }

        # Perform actual write
        # Store original states for components to prevent automatic demotion
        # This preserves manually set "Active" states during quoting/confirmation
        original_states = {}
        if "product_state_id" in vals:
            # Track original states before write
            for product in self:
                original_states[product.id] = product.product_state_id
        
        res = super().write(vals)
        
        # Restore manually set states if they were demoted by automatic processes
        # This prevents automatic resets during quoting workflows
        if "product_state_id" in vals and original_states:
            state_model = self.env["product.state"].sudo()
            new_state = state_model.browse(vals["product_state_id"]) if vals["product_state_id"] else None
            
            for product in self:
                original_state = original_states.get(product.id)
                if original_state and new_state:
                    original_sequence = original_state.sequence
                    new_sequence = new_state.sequence
                    
                    # Only restore if state was demoted (worse state) and this is NOT a manual change
                    # This prevents "Active" from being reset to "End of Lifecycle" during quoting
                    if new_sequence < original_sequence:
                        # Check if this was from an automatic process (not manual)
                        # If it's a manual state change (upgrade), we already handled it above
                        # If it's automatic and demoting, we should preserve the original state
                        is_manual = is_manual_state_change or self.env.context.get(
                            "manual_product_state_change", False
                        )
                        from_exception = self.env.context.get("from_exception_check", False)
                        
                        # Only restore if:
                        # 1. It's NOT a manual change (to avoid interfering with user actions)
                        # 2. It's from an exception check (automatic process)
                        # 3. The demotion is significant (original was much better)
                        if not is_manual and from_exception and (original_sequence - new_sequence) > 1:
                            # Restore the original (better) state to preserve user intent
                            # Use skip_kit_state_update to prevent infinite loops
                            product.with_context(
                                skip_kit_state_update=True,
                                from_exception_check=True
                            ).write({"product_state_id": original_state.id})

        # --- KIT PRODUCT STATE UPDATE (Phantom BOMs only) ---
        # Only update kit states if this write was not triggered by a manual state change
        # This prevents automatic resets of manually set product states during quoting
        skip_kit_state_update = self.env.context.get("skip_kit_state_update", False)
        
        if not skip_kit_state_update:
            # Get BOM lines where any of these products are components
            bom_lines = (
                self.env["mrp.bom.line"]
                .sudo()
                .search([("product_tmpl_id", "in", self.ids)])
            )

            # From those BOM lines, find phantom BOMs (kits)
            phantom_boms = bom_lines.mapped("bom_id").filtered(
                lambda b: b.type == "phantom"
            )

            # Get unique kit products
            kit_templates = phantom_boms.mapped("product_tmpl_id")

            for kit in kit_templates:
                # Skip kit state update if this is a manual state change and the kit
                # state was manually set (preserve user intent)
                if "product_state_id" in vals:
                    # Check if this write is a manual state change
                    # Use context flag if set, otherwise check if upgrading to better state
                    manual_flag = self.env.context.get(
                        "manual_product_state_change", False
                    )
                    if manual_flag or is_manual_state_change:
                        # Skip automatic kit state updates when manually setting component states
                        # to preserve user's manual state changes during quoting
                        continue

                # Fetch all component states from kit's phantom BOMs
                component_states = (
                    kit.bom_ids.filtered(lambda b: b.type == "phantom")
                    .mapped("bom_line_ids.product_tmpl_id.product_state_id")
                    .filtered(lambda s: s)
                )

                if not component_states:
                    continue  # Nothing to evaluate

                # Separate exception vs normal states
                exception_states = component_states.filtered(lambda s: s.trigger_exception)
                normal_states = component_states - exception_states

                if exception_states:
                    # Prioritize highest sequence exception state
                    new_kit_state = max(exception_states, key=lambda s: s.sequence)
                else:
                    # Otherwise, pick highest sequence normal state
                    new_kit_state = max(normal_states, key=lambda s: s.sequence)

                # Only update kit state if it's different and not preserving a manual change
                # Skip automatic demotion if the kit state was manually set
                if kit.product_state_id != new_kit_state:
                    # Check if kit state was manually set by checking if it's in a "better"
                    # state than what we'd calculate (suggesting manual intervention)
                    # Only update if we're not overwriting a manually set "better" state
                    kit_state_sequence = kit.product_state_id.sequence if kit.product_state_id else 0
                    new_state_sequence = new_kit_state.sequence if new_kit_state else 0
                    
                    # Allow update if new state is better (higher sequence) or equal
                    # Prevent automatic demotion (lower sequence) to preserve manual "Active" states
                    if new_state_sequence >= kit_state_sequence:
                        kit.with_context(
                            skip_kit_state_update=True
                        ).write({"product_state_id": new_kit_state.id})

        # --- Exception Checks on SO/DO/MO ---

        # --- Exception workflow triggering for related orders and MOs ---
        # Mark context to indicate these are from exception checks (not manual changes)
        exception_context = self.env.context.copy()
        exception_context.update({"from_exception_check": True})
        
        if state_change_triggers or tech_exception_triggers or relevant_changes:
            related_products = self.product_variant_ids
            if related_products:
                # SALE ORDERS (Direct & BOM-based)
                direct_sale_orders = (
                    self.env["sale.order.line"]
                    .sudo()
                    .search([("product_id", "in", related_products.ids)])
                    .mapped("order_id")
                    .filtered(
                        lambda o: o.state not in ["draft", "cancel"]
                        and not o.ignore_exception
                    )
                )

                # Fetch sale orders via SQL for BOM-based items
                self.env.cr.execute(
                    """
                    SELECT DISTINCT sol.order_id
                    FROM sale_order_line sol
                    JOIN mrp_bom_line bl ON sol.bom_id = bl.bom_id
                    WHERE bl.product_id = ANY(%s)
                    """,
                    [related_products.ids],
                )
                order_ids = [row[0] for row in self.env.cr.fetchall()]

                bom_based_sale_orders = (
                    self.env["sale.order"]
                    .sudo()
                    .browse(order_ids)
                    .filtered(
                        lambda o: o.state not in ["draft", "cancel"]
                        and not o.ignore_exception
                    )
                )

                sale_orders = direct_sale_orders | bom_based_sale_orders
                sale_orders.with_context(exception_context).sale_check_exception()

                # DELIVERY ORDERS
                pickings = sale_orders.mapped("picking_ids").filtered(
                    lambda p: p.state not in ["draft", "cancel", "done"]
                    and p.picking_type_code == "outgoing"
                    and not p.ignore_exception
                )
                pickings.stock_check_exception()

                # MANUFACTURING ORDERS
                direct_mos = (
                    self.env["mrp.production"]
                    .sudo()
                    .search(
                        [
                            ("product_id", "in", related_products.ids),
                            ("state", "not in", ["draft", "cancel", "done"]),
                            ("ignore_exception", "!=", True),
                        ]
                    )
                )

                # Fetch component MOs via SQL
                self.env.cr.execute(
                    """
                    SELECT DISTINCT sm.raw_material_production_id
                    FROM stock_move sm
                    WHERE sm.product_id = ANY(%s)
                    AND sm.raw_material_production_id IS NOT NULL
                    """,
                    [related_products.ids],
                )
                component_mo_ids = [row[0] for row in self.env.cr.fetchall()]

                component_mos = (
                    self.env["mrp.production"]
                    .sudo()
                    .browse(component_mo_ids)
                    .filtered(
                        lambda mo: mo.state not in ["draft", "cancel", "done"]
                        and not mo.ignore_exception
                    )
                )

                mrp_productions = direct_mos | component_mos
                mrp_productions.mrp_check_exception()

        return res

    # END ##########
