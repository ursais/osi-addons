# Import Odoo libs
from odoo import fields, models


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
        res = super().write(vals)

        # --- KIT PRODUCT STATE UPDATE (Phantom BOMs only) ---

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

            # Always force kit state update, even for demotion
            # Skip update if product state was manually set by user
            if kit.product_state_id != new_kit_state and not kit.product_state_manually_set:
                kit.write({"product_state_id": new_kit_state.id})

        # --- Exception Checks on SO/DO/MO ---

        # --- Exception workflow triggering for related orders and MOs ---
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
                sale_orders.sale_check_exception()

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
