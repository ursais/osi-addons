# Import Odoo libs
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

# Constants for state values
STATE_DONE = "done"
STATE_CANCEL = "cancel"
STATE_HOLD = "hold"
STATE_DRAFT = "draft"

# Constants for config parameter keys
CONFIG_USE_BATCH_TRANSFER = "mrp_batch.use_batch_transfer"
CONFIG_SEQUENCE_PICKING_BATCH = "picking.batch"
CONFIG_SEQUENCE_STOCK_LOT_SERIAL = "stock.lot.serial"


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
        "move_raw_ids.state",
        "move_raw_ids.quantity",
        "move_finished_ids.state",
        "workorder_ids.state",
        "product_qty",
        "qty_producing",
        "move_raw_ids.picked",
        "mrp_batch_id.state",
    )
    def _compute_state(self):
        """
        Override to trigger batch state recomputation via dependencies.
        Using proper ORM dependencies instead of manual compute calls.
        """
        return super()._compute_state()

    def _get_batch_transfer_enabled(self):
        """Helper method to check if batch transfer is enabled."""
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CONFIG_USE_BATCH_TRANSFER, "False")
        )
        # Convert string to boolean properly
        return param_value.lower() in ("true", "1", "yes")

    def _link_pickings_to_batches(self):
        """Link all pickings for this MO to its mrp_batch_id batch picking."""
        if not self._get_batch_transfer_enabled():
            return  # skip Batch Pickings

        for mo in self:
            if not mo.mrp_batch_id:
                continue

            pickings = mo.picking_ids.filtered(
                lambda p: p.state not in (STATE_DONE, STATE_CANCEL)
            )
            if not pickings:
                continue

            try:
                # Find existing batch picking for this mrp_batch_id
                batch = self.env["stock.picking.batch"].search(
                    [("mrp_batch_id", "=", mo.mrp_batch_id.id)], limit=1
                )
                if not batch:
                    seq_name = (
                        self.env["ir.sequence"].next_by_code(
                            CONFIG_SEQUENCE_PICKING_BATCH
                        )
                        or "NEW"
                    )
                    batch = self.env["stock.picking.batch"].create(
                        {
                            "name": f"{seq_name}/{mo.mrp_batch_id.name}",
                            "user_id": self.env.user.id,
                            "company_id": mo.company_id.id,
                            "mrp_batch_id": mo.mrp_batch_id.id,
                        }
                    )

                # Add this MO's pickings to the batch
                batch.write({"picking_ids": [(4, pid) for pid in pickings.ids]})

                # Link pickings back to the MO batch
                pickings.write(
                    {
                        "batch_id": batch.id,
                        "mrp_batch_id": mo.mrp_batch_id.id,
                    }
                )

                # Confirm Batch Picking if in draft state
                if batch.state == STATE_DRAFT:
                    batch.action_confirm()
            except Exception as e:
                _logger.error(
                    "Failed to link pickings to batch for MO %s: %s",
                    mo.name,
                    str(e),
                )
                # Continue with other MOs instead of failing completely

    @api.model
    def create(self, vals):
        """Override create to link pickings to batches."""
        mo = super().create(vals)
        if mo.mrp_batch_id:
            mo._link_pickings_to_batches()
        return mo

    def write(self, vals):
        """Override write to handle batch changes and relink pickings."""
        # Track previous batch for re-linking
        old_batches = {mo.id: mo.mrp_batch_id for mo in self}
        res = super().write(vals)

        batches_to_update = set()

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
                batches_to_update.add(old_batch)

            if new_batch:
                # Relink pickings to the new batch
                mo._link_pickings_to_batches()
                batches_to_update.add(new_batch)

        # Batch state will be recomputed automatically via dependencies
        # No need for manual compute calls

        return res

    # END #########
