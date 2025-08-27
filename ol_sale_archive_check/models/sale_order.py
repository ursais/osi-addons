# Import Odoo libs
from odoo import _, api, fields, models
from odoo.tools import html_escape


class SaleOrder(models.Model):
    """
    Add new fields to Sale Order and check archive methods.
    """

    _inherit = "sale.order"

    # COLUMNS #####

    has_archived_products_or_boms = fields.Boolean(
        compute="_compute_has_archived_products_or_boms",
        help="Helper field to show alert if any Product or BoM is archived on the order.",
    )

    # END #########
    # METHODS #########

    @api.depends("order_line.is_archived_or_bom_archived")
    def _compute_has_archived_products_or_boms(self):
        for order in self:
            order.has_archived_products_or_boms = any(
                order.order_line.mapped("is_archived_or_bom_archived")
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Intercept creation to handle chatter logs for duplicated orders."""
        order = super().create(vals_list)

        context_original_order = self.env.context.get("copy_from_order_id")
        if context_original_order:
            original_order = self.browse(context_original_order)
            order._log_archive_status_changes(original_order)

        return order

    def copy(self, default=None):
        """Mark which order we copied from in context so create() can access it."""
        default = default or {}
        self.ensure_one()
        return super(SaleOrder, self.with_context(copy_from_order_id=self.id)).copy(
            default=default
        )

    def _log_archive_status_changes(self, original_order):
        """Compare lines between old and new order for archived products/BOMs and their components."""
        msg_lines = []
        bom_model = self.env["mrp.bom"]

        for old_line, new_line in zip(original_order.order_line, self.order_line):
            # Track if something was flagged for this line
            line_flagged = False

            # --- Check if product archived ---
            if old_line.product_id and not old_line.product_id.active:
                msg_lines.append(
                    f"Product <b>{html_escape(old_line.product_id.display_name)}</b> was archived."
                )
                line_flagged = True

            # --- Check if BOM archived ---
            if old_line.bom_id and not old_line.bom_id.active:
                replacement_bom = bom_model.search(
                    [
                        ("product_id", "=", old_line.product_id.id),
                        ("active", "=", True),
                    ],
                    limit=1,
                )

                if replacement_bom:
                    new_line.bom_id = replacement_bom
                    differences = self._compare_boms(old_line.bom_id, replacement_bom)
                    if differences:
                        msg_lines.append(
                            f"BoM for product <b>{html_escape(old_line.product_id.display_name)}</b> "
                            f"was replaced:<br/>"
                            + "<br/>".join(
                                f"- {html_escape(diff)}" for diff in differences
                            )
                        )
                else:
                    msg_lines.append(
                        f"BoM for product <b>{html_escape(old_line.product_id.display_name)}</b> was archived "
                        "and no replacement BoM found."
                    )
                line_flagged = True

            # --- Check if any BOM component archived ---
            if old_line.bom_id:
                archived_components = old_line.bom_id.bom_line_ids.filtered(
                    lambda bl: not bl.product_id.active
                )
                for comp in archived_components:
                    msg_lines.append(
                        f"Component <b>{html_escape(comp.product_id.display_name)}</b> in BoM "
                        f"for <b>{html_escape(old_line.product_id.display_name)}</b> was archived."
                    )
                if archived_components:
                    line_flagged = True

            # If anything triggered, flag this line
            if line_flagged:
                new_line.is_archived_or_bom_archived = True

        if msg_lines:
            self.message_post(body="<br/>".join(msg_lines), body_is_html=True)

    def _compare_boms(self, bom1, bom2):
        """Compare BOM components and operations, return list of human-readable differences."""
        differences = []

        # --- Compare Components ---
        comp_map1 = {l.product_id.id: l for l in bom1.bom_line_ids}
        comp_map2 = {l.product_id.id: l for l in bom2.bom_line_ids}

        comp1_ids = set(comp_map1.keys())
        comp2_ids = set(comp_map2.keys())

        # Added components
        for pid in comp2_ids - comp1_ids:
            prod = comp_map2[pid].product_id
            differences.append(
                f"Component ADD: {prod.display_name} — Qty: {comp_map2[pid].product_qty} {comp_map2[pid].product_uom_id.display_name}"
            )

        # Removed components
        for pid in comp1_ids - comp2_ids:
            prod = comp_map1[pid].product_id
            differences.append(
                f"Component REMOVE: {prod.display_name} — Qty: {comp_map1[pid].product_qty} {comp_map1[pid].product_uom_id.display_name}"
            )

        # Changed components
        for pid in comp1_ids & comp2_ids:
            old_line = comp_map1[pid]
            new_line = comp_map2[pid]
            if (
                old_line.product_qty != new_line.product_qty
                or old_line.product_uom_id.id != new_line.product_uom_id.id
            ):
                differences.append(
                    f"Component CHANGE: {old_line.product_id.display_name} — "
                    f"Qty: {old_line.product_qty} {old_line.product_uom_id.display_name} → {new_line.product_qty} {new_line.product_uom_id.display_name}"
                )

        # --- Compare Operations ---
        op_map1 = {o.name: o for o in bom1.operation_ids}
        op_map2 = {o.name: o for o in bom2.operation_ids}

        op1_names = set(op_map1.keys())
        op2_names = set(op_map2.keys())

        # Added operations
        for name in op2_names - op1_names:
            op = op_map2[name]
            differences.append(
                f"Operation added: {op.name} — Workcenter: {op.workcenter_id.display_name}, Time: {op.time_cycle_manual} min"
            )

        # Removed operations
        for name in op1_names - op2_names:
            op = op_map1[name]
            differences.append(
                f"Operation removed: {op.name} — Workcenter: {op.workcenter_id.display_name}, Time: {op.time_cycle_manual} min"
            )

        # Changed operations
        for name in op1_names & op2_names:
            old_op = op_map1[name]
            new_op = op_map2[name]
            changes = []
            if old_op.workcenter_id.id != new_op.workcenter_id.id:
                changes.append(
                    f"Workcenter: {old_op.workcenter_id.display_name} → {new_op.workcenter_id.display_name}"
                )
            if old_op.time_cycle_manual != new_op.time_cycle_manual:
                changes.append(
                    f"Time: {old_op.time_cycle_manual} → {new_op.time_cycle_manual} min"
                )
            if old_op.sequence != new_op.sequence:
                changes.append(f"Sequence: {old_op.sequence} → {new_op.sequence}")
            if changes:
                differences.append(f"Operation changed: {name} — " + ", ".join(changes))

        return differences

    # END #########
