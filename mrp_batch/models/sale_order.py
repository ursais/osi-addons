# Import Odoo libs
from odoo import fields, models, _, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # COLUMNS #########

    mrp_batch_count = fields.Integer(
        string="MO Batch Count",
        compute="_compute_mrp_production_batch_id_count",
    )
    is_mrp_warning = fields.Boolean(compute="_compute_is_mrp_warning")

    # END #########
    # METHODS #####

    def _compute_is_mrp_warning(self):
        for so in self:
            is_mrp_warning = False

            # Check if there are any related manufacturing orders (mrp_production_ids)
            # and if any of those orders are planned or in specific states
            if so.mrp_production_ids and so.mrp_production_ids.filtered(
                lambda l: l.is_planned or l.state in ("progress", "to_close", "done")
            ):
                is_mrp_warning = True

            so.is_mrp_warning = is_mrp_warning

    @api.depends(
        "procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids"
    )
    def _compute_mrp_production_ids(self):
        res = super()._compute_mrp_production_ids()
        data = self.env["procurement.group"]._read_group(
            [("sale_id", "in", self.ids)], ["sale_id"], ["id:recordset"]
        )
        mrp_productions = {}
        for sale, procurement_groups in data:
            mrp_productions[sale.id] = (
                procurement_groups.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids
                | procurement_groups.mrp_production_ids
                | procurement_groups.stock_move_ids.created_production_id.linked_mo_ids
            )
        for sale in self:
            mrp_production_ids = mrp_productions.get(
                sale.id, self.env["mrp.production"]
            )
            sale.mrp_production_count = len(mrp_production_ids)
            sale.mrp_production_ids = mrp_production_ids
        return res

    def split_mo(self):
        """
        Split MOs linked to this sale order into single-qty MOs,
        give each new MO its own procurement.group, then confirm each MO
        so Odoo generates the component/internal transfers naturally.

        Batch creation behavior:
          - If ir.config_parameter 'mrp_batch.batch_mode' == 'single' -> create one batch for the whole order
          - Otherwise -> do NOT create a batch per MO (no automatic per-MO batch creation)
        """
        batch_obj = self.env["mrp.production.batch"]
        group_obj = self.env["procurement.group"]
        batch_mode = (
            self.env["ir.config_parameter"].sudo().get_param("mrp_batch.batch_mode")
        )

        for order in self:
            existing_batch = None
            if batch_mode == "single":
                # one batch for the whole order (created once)
                existing_batch = batch_obj.sudo().create(
                    {"responsible_id": order.env.user.id}
                )

            for mo in order.mrp_production_ids:
                # Skip MOs that are already done or cancelled - they should not be split
                # Splitting done MOs creates invalid backorders in draft state
                if mo.state in ("done", "cancel"):
                    continue

                # only split serial-tracked products that allow splitting
                if (
                    mo.product_id.tracking != "serial"
                    or not mo.product_id.is_allow_split_mo
                ):
                    continue

                if mo.product_qty <= 1:
                    continue

                # ensure there is a procurement group for the original MO
                if not mo.procurement_group_id:
                    mo.procurement_group_id = group_obj.sudo().create({"name": mo.name})

                remaining_mo = mo
                new_mos = []
                delivery_move = mo.move_dest_ids

                # native split: split off single-qty MOs
                for i in range(int(mo.product_qty) - 1):
                    # _split_productions returns new production records; use sudo to avoid rights issues
                    result = remaining_mo.sudo()._split_productions(
                        amounts={remaining_mo: [1]}
                    )
                    new_created = result[0]
                    remaining_mo = result[-1]
                    new_mos.append(new_created)

                # include the last (remainder) MO
                new_mos.append(remaining_mo)

                # Assign a fresh procurement.group to each split MO and (optionally) assign the single batch
                for idx, new_mo in enumerate(new_mos, start=1):
                    new_group = group_obj.sudo().create({"name": f"{mo.name}-{idx}"})
                    new_mo.sudo().write({"procurement_group_id": new_group.id})

                    # ONLY assign a batch if batch_mode == "single"
                    if existing_batch:
                        new_mo.sudo().write({"mrp_batch_id": existing_batch.id})

                # Now: ensure any existing moves belong to the new group, then confirm each MO
                for new_mo in new_mos:
                    # If the split copied moves, reassign their group/origin so pickings split correctly
                    moves = new_mo.move_raw_ids | new_mo.move_finished_ids
                    if moves:
                        moves.sudo().write(
                            {
                                "group_id": new_mo.procurement_group_id.id,
                                "origin": new_mo.name,
                            }
                        )

                    # Update move quantities to match split qty
                    for move in new_mo.move_finished_ids:
                        move.product_uom_qty = new_mo.product_qty

                    # Confirm the MO if it's still draft so Odoo generates/updates moves & pickings.
                    # We toggle ignore_exception to mimic your previous safe-confirm pattern.
                    # Confirm the MO if it's still draft so Odoo generates/updates moves & pickings.
                    # We toggle ignore_exception to mimic your previous safe-confirm pattern.
                    # Only confirm if MO is in draft state and has valid configuration
                    if new_mo.state == "draft":
                        # Ensure serial number is assigned before confirmation for serial-tracked products
                        if new_mo.product_id.tracking == "serial" and not new_mo.lot_producing_id:
                            lot = self.env["stock.lot"].create(
                                {
                                    "name": self.env["ir.sequence"].next_by_code(
                                        "stock.lot.serial"
                                    )
                                    or "/",
                                    "product_id": new_mo.product_id.id,
                                    "company_id": new_mo.company_id.id,
                                }
                            )
                            new_mo.lot_producing_id = lot.id
                        
                        # Only confirm if MO has valid moves and quantities
                        if new_mo.product_qty > 0 and (new_mo.move_raw_ids or new_mo.move_finished_ids):
                            new_mo.sudo().write({"ignore_exception": True})
                            new_mo.sudo().action_confirm()
                            new_mo.sudo().write({"ignore_exception": False})
                        else:
                            # If MO has no valid moves/quantities, cancel it instead
                            new_mo.sudo().action_cancel()

                    # Ensure pickings that were created for this MO are at least tagged with the group/origin
                    if new_mo.picking_ids:
                        new_mo.picking_ids.sudo().write(
                            {
                                "group_id": new_mo.procurement_group_id.id,
                                "origin": new_mo.name,
                            }
                        )

                # keep a reference on the original MO to the new MOs
                mo.sudo().write({"linked_mo_ids": [(6, 0, [m.id for m in new_mos])]})

                # Assign batch to original MO and its backorders
                if not mo.mrp_batch_id:
                    mo.write(
                        {
                            "mrp_batch_id": (
                                existing_batch.id
                                if batch_mode == "single"
                                else batch_obj.create(
                                    {"responsible_id": self.env.user.id}
                                ).id
                            ),
                            "ignore_exception": False,
                        }
                    )
                    # mo.backorder_ids.write({"mrp_batch_id": mo.mrp_batch_id.id})
                    mo.linked_mo_ids.filtered(lambda l: not l.mrp_batch_id).write(
                        {
                            "mrp_batch_id": mo.mrp_batch_id.id,
                            "ignore_exception": False,
                        }
                    )

                # Reset finished moves destination
                finished_product_moves = mo.linked_mo_ids.move_finished_ids.filtered(
                    lambda m: not m.move_dest_ids
                )
                finished_product_moves.move_dest_ids = [(6, 0, [delivery_move.id])]

            # optional commit so successive operations see persisted state (keeps DB in a stable state)
            self.env.cr.commit()

        return True

    # Methods for Batch Smart Button
    def _compute_mrp_production_batch_id_count(self):
        # Computes the count of unique batch IDs linked to the
        # MOs in `mrp_production_ids`.
        for record in self:
            # Collects batch IDs for each MO in `mrp_production_ids`.
            batch_id = [batch.id for batch in record.mrp_production_ids.mrp_batch_id]
            # Sets `mrp_batch_count` to the number of unique batches found.
            record.mrp_batch_count = len(batch_id)

    def action_view_mrp_production_batch(self):
        # Ensures the method is called on a single record.
        self.ensure_one()
        # Defines the base action for viewing the manufacturing production batch.
        action = {
            "res_model": "mrp.production.batch",
            "type": "ir.actions.act_window",
        }
        # Checks if there is only one batch ID in `mrp_production_ids`.
        if len([batch.id for batch in self.mrp_production_ids.mrp_batch_id]) == 1:
            # If there is a single batch, open it in form view.
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.mrp_production_ids.mrp_batch_id.id,
                }
            )
        else:
            # If there are multiple batches, open them in tree and form view with a
            # domain filter.
            action.update(
                {
                    "name": _(
                        "Manufacturing Production Batch Generated by %s", self.name
                    ),
                    "domain": [("id", "in", self.mrp_production_ids.mrp_batch_id.ids)],
                    "view_mode": "tree,form",
                }
            )
        return action

    # END #########
