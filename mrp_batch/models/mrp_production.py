# Import Odoo libs
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    """Inherit Manufacturing Orders to add Batch Functionality."""

    _inherit = "mrp.production"

    # COLUMNS #########

    mrp_batch_id = fields.Many2one(
        "mrp.production.batch",
        string="MRP Batch",
        domain="[('state', 'not in', ('done','cancel','hold'))]",
        copy=False,
    )
    mrp_batch_state = fields.Selection(
        related="mrp_batch_id.state",
        readonly=True,
        string="Batch Status",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
    )
    sale_order_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
    )
    sale_state = fields.Selection(
        related="sale_order_id.state",
        store=True,
    )
    linked_mo_ids = fields.Many2many(
        comodel_name="mrp.production",
        string="Linked MO",
        relation="rel_mrp_production_group",
        column1="mo_id",
        column2="linked_mo_id",
    )

    @api.depends(
        "procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id"
    )
    def _compute_sale_order_count(self):
        # Call super first
        super()._compute_sale_order_count()
        for mo in self:
            # If super left it 0 but we have sale_order_id, count it
            if mo.sale_order_count == 0 and mo.sale_order_id:
                mo.sale_order_count = 1

    def action_view_sale_orders(self):
        self.ensure_one()
        # Get the original action from super
        super().action_view_sale_orders()

        # Collect sale orders from procurement group chain
        sale_order_ids = set(
            self.procurement_group_id.mrp_production_ids.move_dest_ids.group_id.sale_id.ids
        )

        # Include sale_order_id on the MO if set
        if self.sale_order_id:
            sale_order_ids.add(self.sale_order_id.id)

        sale_order_ids = list(sale_order_ids)

        # Build the action
        action = {
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }
        if len(sale_order_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": sale_order_ids[0],
                }
            )
        else:
            action.update(
                {
                    "name": _("Sources Sale Orders of %s", self.name),
                    "domain": [("id", "in", sale_order_ids)],
                    "view_mode": "tree,form",
                }
            )
        return action

    def button_plan(self):
        """
        Override button_plan to generate a serial number if
        the product is serialized
        """
        res = super().button_plan()

        for order in self:
            if order.product_id.tracking == "serial" and not order.lot_producing_id:
                # Generate serial number for the finished product during plan
                if order.product_id.tracking == "serial":
                    lot = self.env["stock.lot"].create(
                        {
                            "name": self.env["ir.sequence"].next_by_code(
                                "stock.lot.serial"
                            )
                            or "/",
                            "product_id": order.product_id.id,
                            "company_id": order.company_id.id,
                        }
                    )
                    order.lot_producing_id = lot.id

        return res

    def action_remove_batch(self):
        if self.filtered(lambda mo: not mo.mrp_batch_id):
            raise UserError(
                "No batch found to remove or batch has already been removed."
            )
        if self.mapped("mrp_batch_id").filtered(
            lambda b: b.state in ("done", "cancel", "hold")
        ):
            raise UserError("Some Manufacturing Batches cannot be removed.")

        for mo in self:
            # Unlink pickings from batch picking
            mo.picking_ids.write({"batch_id": False})
            mo.mrp_batch_id = False

    def action_open_wizard(self):
        # Check if any record already has an assigned batch
        if any(record.mrp_batch_id for record in self):
            raise UserError(
                "A batch has already been created for one or more selected records."
            )

        # Check for records in 'done' or 'cancel' state
        if any(record.state in ["done", "cancel"] for record in self):
            raise UserError(
                "You cannot create a batch for records that are in 'Done' or 'Cancel' state."
            )

        # Return the action only after all checks are completed
        return {
            "name": "Create Batch",
            "type": "ir.actions.act_window",
            "res_model": "mrp.production.batch.wizard",
            "view_mode": "form",
            "target": "new",
        }

    @api.depends(
        "move_raw_ids.state",
        "move_raw_ids.quantity",
        "move_finished_ids.state",
        "workorder_ids.state",
        "product_qty",
        "qty_producing",
        "move_raw_ids.picked",
    )
    def _compute_state(self):
        # Call the original compute logic
        res = super()._compute_state()

        # Trigger batch state computation for related batches
        for production in self:
            if production.mrp_batch_id:
                production.mrp_batch_id._compute_batch_state()

        return res

    def _link_pickings_to_batches(self):
        """Link all pickings for this MO to its mrp_batch_id batch picking."""
        use_batch_transfer = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mrp_batch.use_batch_transfer")
        )
        if use_batch_transfer != "True":
            return  # skip Batch Pickings

        for mo in self:
            if not mo.mrp_batch_id:
                continue

            pickings = mo.picking_ids.filtered(
                lambda p: p.state not in ("done", "cancel")
            )
            if not pickings:
                continue

            # Find existing batch picking for this mrp_batch_id
            batch = self.env["stock.picking.batch"].search(
                [("mrp_batch_id", "=", mo.mrp_batch_id.id)], limit=1
            )
            if not batch:
                seq_name = (
                    self.env["ir.sequence"].next_by_code("picking.batch") or "NEW"
                )
                batch = self.env["stock.picking.batch"].create(
                    {
                        "name": f"{seq_name}/{mo.mrp_batch_id.name}",
                        "user_id": self.env.user.id,
                        "company_id": mo.company_id.id,
                        "mrp_batch_id": mo.mrp_batch_id.id,
                    }
                )

            # Add this MO’s pickings to the batch
            batch.write({"picking_ids": [(4, pid) for pid in pickings.ids]})

            # Link pickings back to the MO batch
            pickings.write(
                {
                    "batch_id": batch.id,
                    "mrp_batch_id": mo.mrp_batch_id.id,
                }
            )

            # Confirm Batch Picking if in draft state
            if batch.state == "draft":
                batch.action_confirm()

    @api.model
    def create(self, vals):
        mo = super().create(vals)
        if mo.mrp_batch_id:
            mo._link_pickings_to_batches()
        return mo

    def write(self, vals):
        # Track previous batch for re-linking
        old_batches = {mo.id: mo.mrp_batch_id for mo in self}
        res = super().write(vals)

        batches_to_recompute = set()

        for mo in self:
            old_batch = old_batches.get(mo.id)
            new_batch = mo.mrp_batch_id

            if old_batch and old_batch != new_batch:
                # Remove this MO's pickings from the old batch picking(s)
                for picking in mo.picking_ids:
                    if picking.batch_id and picking.batch_id.mrp_batch_id == old_batch:
                        picking.write(
                            {
                                "batch_id": False,
                                "mrp_batch_id": False,
                            }
                        )
                batches_to_recompute.add(old_batch)

            if new_batch:
                # Relink pickings to the new batch
                mo._link_pickings_to_batches()
                batches_to_recompute.add(new_batch)

        # Recompute batch states
        if batches_to_recompute:
            for batch in batches_to_recompute:
                batch._compute_batch_state()

        return res
    def _split_productions(self, amounts=None, cancel_remaining=False):
        """
        Override _split_productions to properly handle backorders when splitting
        done MOs, ensuring serial numbers and state are correctly initialized.

        When splitting a done MO:
        - If the split represents work that was already completed, the backorder
          should be cancelled (not created as draft)
        - If the split represents work that needs to be done, the backorder should
          be properly initialized with serial numbers and confirmed state
        """
        # Call super to perform the split
        result = super()._split_productions(
            amounts=amounts, cancel_remaining=cancel_remaining
        )

        # Process each production in the result to ensure proper initialization
        for production in result:
            # Skip if production is cancelled or already properly initialized
            if production.state == "cancel":
                continue

            # If the original MO was done and this is a backorder, handle it appropriately
            # Check if this is a backorder created from a done MO
            # Check if this is a backorder created from a done MO
            # If original MO state was 'done', backorders should typically be cancelled
            # unless they represent actual work that needs to be completed
            original_state_done = self.state == "done"
            if production.state == "draft" and production.origin:
                # Check if this backorder should represent work that was never done
                # If the original MO was done and we're splitting, the backorder should
                # typically be cancelled if it represents work that wasn't actually completed
                # However, if it represents work that needs to be done, it should be initialized

                # For serial-tracked products, ensure serial number is assigned
                if production.product_id.tracking == "serial":
                    if not production.lot_producing_id:
                        # Generate serial number for the backorder
                        lot = self.env["stock.lot"].create(
                            {
                                "name": self.env["ir.sequence"].next_by_code(
                                    "stock.lot.serial"
                                )
                                or "/",
                                "product_id": production.product_id.id,
                                "company_id": production.company_id.id,
                            }
                        )
                        production.lot_producing_id = lot.id

                # If the original MO was done, this backorder typically represents work
                # that was never actually completed, so it should be cancelled
                # Exception: if it has valid moves and quantities, it might represent
                # legitimate work that needs to be done
                if original_state_done:
                    # For done MOs, backorders with no moves or zero qty should be cancelled
                    if (
                        not production.move_raw_ids
                        and not production.move_finished_ids
                    ) or production.product_qty <= 0:
                        production.action_cancel()
                        continue
                    # Even if it has moves, if the original MO was fully completed,
                    # the backorder might be invalid - but we'll let it through if it has
                    # valid configuration to allow manual review
                
                # If the backorder has no moves or quantities are zero, cancel it
                if (
                    not production.move_raw_ids
                    and not production.move_finished_ids
                ) or production.product_qty <= 0:
                    production.action_cancel()
                    continue

                # Ensure the backorder has proper procurement group if missing
                if not production.procurement_group_id and self.procurement_group_id:
                    production.procurement_group_id = self.procurement_group_id

                # Copy important fields from original MO if missing
                if not production.sale_order_id and self.sale_order_id:
                    production.sale_order_id = self.sale_order_id
                if not production.sale_order_line_id and self.sale_order_line_id:
                    production.sale_order_line_id = self.sale_order_line_id

        return result


    
    @api.model
    def fix_migration_split_mos(self):
        """
        Fix Manufacturing Orders that were incorrectly split during migration,
        leaving backorders in draft state without serial numbers.

        This method identifies MOs that:
        - Are in draft state
        - Have an origin (indicating they are backorders from a split)
        - Are for serial-tracked products
        - Have no lot_producing_id assigned
        - Have a linked MO that is done (indicating the original was completed)

        For such MOs, it will:
        - Cancel them if they represent work that was never done (no moves, zero qty)
        - Or properly initialize them if they represent legitimate work
        """
        # Find problematic MOs: draft state, serial-tracked, no lot, has origin
        problematic_mos = self.search([
            ("state", "=", "draft"),
            ("product_id.tracking", "=", "serial"),
            ("lot_producing_id", "=", False),
            ("origin", "!=", False),
        ])

        if not problematic_mos:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Fix Complete"),
                    "message": _("No problematic Manufacturing Orders found."),
                    "type": "success",
                    "sticky": False,
                },
            }

        cancelled_count = 0
        fixed_count = 0
        error_count = 0

        for mo in problematic_mos:
            try:
                # Check if this MO is linked to a done MO, indicating it's a backorder
                # from a completed MO that was incorrectly split
                linked_done_mos = mo.linked_mo_ids.filtered(lambda m: m.state == "done")
                is_backorder_from_done = linked_done_mos or (
                    mo.origin
                    and self.search_count([
                        ("name", "=", mo.origin.split("/")[0] if "/" in mo.origin else mo.origin),
                        ("state", "=", "done"),
                    ]) > 0
                )

                # If backorder from done MO with no moves/zero qty, cancel it
                if is_backorder_from_done and (
                    not mo.move_raw_ids and not mo.move_finished_ids or mo.product_qty <= 0
                ):
                    mo.action_cancel()
                    cancelled_count += 1
                    continue

                # Otherwise, try to fix it by assigning serial number and confirming
                if mo.product_qty > 0 and (mo.move_raw_ids or mo.move_finished_ids):
                    # Generate serial number
                    lot = self.env["stock.lot"].create(
                        {
                            "name": self.env["ir.sequence"].next_by_code("stock.lot.serial")
                            or "/",
                            "product_id": mo.product_id.id,
                            "company_id": mo.company_id.id,
                        }
                    )
                    mo.lot_producing_id = lot.id

                    # Ensure procurement group exists
                    if not mo.procurement_group_id:
                        group_obj = self.env["procurement.group"]
                        mo.procurement_group_id = group_obj.sudo().create({"name": mo.name})

                    # Try to confirm if possible
                    try:
                        mo.sudo().write({"ignore_exception": True})
                        mo.sudo().action_confirm()
                        mo.sudo().write({"ignore_exception": False})
                        fixed_count += 1
                    except Exception:
                        # If confirmation fails, at least we assigned the serial number
                        error_count += 1
                else:
                    # No valid moves/quantities, cancel it
                    mo.action_cancel()
                    cancelled_count += 1

            except Exception as e:
                error_count += 1
                # Log error but continue processing
                _logger
                _logger.error(
                    "Error fixing MO %s: %s", mo.name, str(e)
                )

        message = _(
            "Processing complete: %d cancelled, %d fixed, %d errors"
        ) % (cancelled_count, fixed_count, error_count)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Fix Complete"),
                "message": message,
                "type": "success" if error_count == 0 else "warning",
                "sticky": False,
            },
        }

    # END #########
