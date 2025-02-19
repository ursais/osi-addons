# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import UserError


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

    # END #########
    # METHODS #####

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
        if self.filtered(lambda batch: not batch.mrp_batch_id):
            raise UserError(
                "No batch found to remove or batch has already been removed."
            )
        if self.mapped("mrp_batch_id").filtered(
            lambda batch: batch.state in ("done", "cancel", "hold")
        ):
            raise UserError("Some manufacting Batch you can't removed.")
        self.mrp_batch_id = False

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

    # END #########
