# Import Odoo libs
from odoo import models


class MrpBom(models.Model):
    """
    Add methods to trigger check archive and bom change on sale orders.
    """

    _inherit = "mrp.bom"

    # METHODS #########

    def _compare_boms_snapshot(self, old_lines, old_ops, new_lines, new_ops):
        """Compare BoM components/operations snapshot vs current, return human-readable diffs."""
        differences = []

        # --- Components ---
        comp_map_old = {pid: (qty, uom) for pid, qty, uom in old_lines}
        comp_map_new = {
            l.product_id.id: (l.product_qty, l.product_uom_id.id) for l in new_lines
        }

        old_ids = set(comp_map_old.keys())
        new_ids = set(comp_map_new.keys())

        # Added
        for pid in new_ids - old_ids:
            prod = new_lines.filtered(lambda l: l.product_id.id == pid).product_id
            qty, uom = comp_map_new[pid]
            differences.append(
                f"Component ADD: {prod.display_name} — Qty: {qty} {prod.uom_id.browse(uom).display_name}"
            )

        # Removed
        for pid in old_ids - new_ids:
            qty, uom = comp_map_old[pid]
            prod = self.env["product.product"].browse(pid)
            differences.append(
                f"Component REMOVE: {prod.display_name} — Qty: {qty} {prod.uom_id.browse(uom).display_name}"
            )

        # Changed
        for pid in old_ids & new_ids:
            old_qty, old_uom = comp_map_old[pid]
            new_qty, new_uom = comp_map_new[pid]
            if old_qty != new_qty or old_uom != new_uom:
                prod = self.env["product.product"].browse(pid)
                differences.append(
                    f"Component CHANGE: {prod.display_name} — "
                    f"Qty: {old_qty} {self.env['uom.uom'].browse(old_uom).display_name} → "
                    f"{new_qty} {self.env['uom.uom'].browse(new_uom).display_name}"
                )

        # --- Operations ---
        op_map_old = {name: (wid, time, seq) for name, wid, time, seq in old_ops}
        op_map_new = {
            o.name: (o.workcenter_id.id, o.time_cycle_manual, o.sequence)
            for o in new_ops
        }

        old_names = set(op_map_old.keys())
        new_names = set(op_map_new.keys())

        # Added
        for name in new_names - old_names:
            wid, time, seq = op_map_new[name]
            wc = self.env["mrp.workcenter"].browse(wid)
            differences.append(
                f"Operation ADD: {name} — Workcenter: {wc.display_name}, Time: {time} min, Seq: {seq}"
            )

        # Removed
        for name in old_names - new_names:
            wid, time, seq = op_map_old[name]
            wc = self.env["mrp.workcenter"].browse(wid)
            differences.append(
                f"Operation REMOVE: {name} — Workcenter: {wc.display_name}, Time: {time} min, Seq: {seq}"
            )

        # Changed
        for name in old_names & new_names:
            old_wid, old_time, old_seq = op_map_old[name]
            new_wid, new_time, new_seq = op_map_new[name]
            changes = []
            if old_wid != new_wid:
                changes.append(
                    f"Workcenter: {self.env['mrp.workcenter'].browse(old_wid).display_name} → "
                    f"{self.env['mrp.workcenter'].browse(new_wid).display_name}"
                )
            if old_time != new_time:
                changes.append(f"Time: {old_time} → {new_time} min")
            if old_seq != new_seq:
                changes.append(f"Seq: {old_seq} → {new_seq}")
            if changes:
                differences.append(f"Operation CHANGE: {name} — " + ", ".join(changes))

        return differences

    def _log_bom_changes(self, bom, differences):
        complete_substate = self.env.ref("ol_sale_substate.base_substate__complete")
        sale_orders = self.env["sale.order"].search(
            [
                ("substate_id", "!=", complete_substate.id),
                ("order_line.bom_id", "=", bom.id),
            ]
        )

        if sale_orders:
            msg = (
                f"BoM for product <b>{bom.product_id.display_name}</b> changed:<br/>"
                + "<br/>".join(f"- {diff}" for diff in differences)
            )
            for order in sale_orders:
                order.message_post(body=msg, body_is_html=True)
                order.sale_check_exception()

    def write(self, vals):
        # Track old state (lines + operations) before write
        before_snapshots = {
            b.id: {
                "lines": [
                    (l.product_id.id, l.product_qty, l.product_uom_id.id)
                    for l in b.bom_line_ids
                ],
                "ops": [
                    (o.name, o.workcenter_id.id, o.time_cycle_manual, o.sequence)
                    for o in b.operation_ids
                ],
            }
            for b in self
        }

        was_active = {b.id: b.active for b in self}
        res = super().write(vals)

        # Case 1: BOM archived
        if "active" in vals and vals["active"] is False:
            archived_boms = self.filtered(lambda b: was_active.get(b.id))
            if archived_boms:
                self.with_delay()._trigger_sale_order_archive_check(archived_boms)

        # Case 2: Lines or operations changed
        if {"bom_line_ids", "operation_ids"} & set(vals.keys()):
            for bom in self.filtered(lambda b: b.active):
                old = before_snapshots.get(bom.id)
                if old:
                    differences = self._compare_boms_snapshot(
                        old["lines"], old["ops"], bom.bom_line_ids, bom.operation_ids
                    )
                    if differences:
                        self.with_delay()._log_bom_changes(bom, differences)

        return res

    def _trigger_sale_order_archive_check(self, boms):
        active_boms = boms.filtered(lambda b: b.product_id and b.product_id.active)
        if not active_boms:
            return

        complete_substate = self.env.ref("ol_sale_substate.base_substate__complete")
        sale_orders = self.env["sale.order"].search(
            [
                ("substate_id", "!=", complete_substate.id),
                ("order_line.bom_id", "in", boms.ids),
            ]
        )

        for order in sale_orders:
            # Pass the original order as "old state" to compare against
            order._log_archive_status_changes(order)
            order.sale_check_exception()

    # END #########
