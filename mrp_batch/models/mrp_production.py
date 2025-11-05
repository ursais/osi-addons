# Import Odoo libs
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

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
        """Remove batch assignment from manufacturing orders."""
        if not self:
            raise ValidationError(_("No manufacturing orders selected."))
        
        if self.filtered(lambda mo: not mo.mrp_batch_id):
            raise UserError(
                _("No batch found to remove or batch has already been removed.")
            )
        invalid_batches = self.mapped("mrp_batch_id").filtered(
            lambda b: b.state in ("done", "cancel", "hold")
        )
        if invalid_batches:
            raise UserError(
                _("Some Manufacturing Batches cannot be removed. Batch(es): %s")
                % ", ".join(invalid_batches.mapped("name"))
            )

        for mo in self:
            try:
                # Unlink pickings from batch picking
                mo.picking_ids.write({"batch_id": False})
                mo.mrp_batch_id = False
            except Exception as e:
                _logger.error(
                    "Error removing batch from MO %s: %s", mo.name, str(e), exc_info=True
                )
                raise UserError(
                    _("Error removing batch from Manufacturing Order %s: %s")
                    % (mo.name, str(e))
                ) from e

    def action_open_wizard(self):
        """Open wizard to create batch for selected manufacturing orders."""
        if not self:
            raise ValidationError(_("No manufacturing orders selected."))
        
        # Check if any record already has an assigned batch
        records_with_batch = self.filtered("mrp_batch_id")
        if records_with_batch:
            raise UserError(
                _("A batch has already been created for one or more selected records: %s")
                % ", ".join(records_with_batch.mapped("name"))
            )

        # Check for records in 'done' or 'cancel' state
        invalid_states = self.filtered(lambda r: r.state in ("done", "cancel"))
        if invalid_states:
            raise UserError(
                _("You cannot create a batch for records that are in 'Done' or 'Cancel' state: %s")
                % ", ".join(invalid_states.mapped("name"))
            )

        # Return the action only after all checks are completed
        return {
            "name": _("Create Batch"),
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
        "mrp_batch_id",
    )
    def _compute_state(self):
        """Compute production state and trigger batch state update."""
        # Call the original compute logic
        res = super()._compute_state()

        # Trigger batch state computation for related batches
        # Use mapped to avoid N+1 queries
        batches = self.mapped("mrp_batch_id")
        if batches:
            # Let ORM handle the computation through dependencies
            batches._compute_batch_state()

        return res

    def _link_pickings_to_batches(self):
        """Link all pickings for this MO to its mrp_batch_id batch picking."""
        use_batch_transfer = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mrp_batch.use_batch_transfer", "False")
        )
        if use_batch_transfer.lower() not in ("true", "1", "yes"):
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
        """Override write to handle batch changes and relink pickings."""
        # Track previous batch for re-linking
        old_batches = {mo.id: mo.mrp_batch_id for mo in self}
        res = super().write(vals)

        batches_to_recompute = set()

        for mo in self:
            old_batch = old_batches.get(mo.id)
            new_batch = mo.mrp_batch_id

            if old_batch and old_batch != new_batch:
                # Remove this MO's pickings from the old batch picking(s)
                pickings_to_update = mo.picking_ids.filtered(
                    lambda p: p.batch_id and p.batch_id.mrp_batch_id == old_batch
                )
                if pickings_to_update:
                    pickings_to_update.write(
                        {
                            "batch_id": False,
                            "mrp_batch_id": False,
                        }
                    )
                batches_to_recompute.add(old_batch)

            if new_batch:
                # Relink pickings to the new batch
                try:
                    mo._link_pickings_to_batches()
                    batches_to_recompute.add(new_batch)
                except Exception as e:
                    _logger.error(
                        "Error linking pickings to batch for MO %s: %s",
                        mo.name,
                        str(e),
                        exc_info=True,
                    )

        # Recompute batch states - let ORM handle it through dependencies
        if batches_to_recompute:
            # Use _compute_batch_state directly on recordset to avoid N+1
            self.env["mrp.production.batch"].browse(list(batches_to_recompute))._compute_batch_state()

        return res

    # END #########
