# Import Odoo libs
from odoo import _, api, fields, models
from odoo.tools import float_is_zero
from odoo.exceptions import ValidationError


class RepairBatch(models.Model):
    _name = "repair.batch"
    _description = "Repair batch"

    @api.model
    def _default_picking_type_id(self):
        return self._get_picking_type().get((self.env.company, self.env.user))

    # COLUMNS ###

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Helpdesk Ticket",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
    )
    tracking = fields.Selection(
        string="Serial/Lot Tracking",
        related="product_id.tracking",
    )
    qty = fields.Float(
        string="Quantity",
        default=1.0,
    )
    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Serial Numbers",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("under_repair", "Under Repair"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        default="draft",
    )
    repair_ids = fields.One2many(
        comodel_name="repair.order",
        inverse_name="repair_batch_id",
        string="Repairs",
    )
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="SO Line",
    )
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
    )
    repair_count = fields.Integer(
        string="Repair Count",
        compute="_compute_repair_count",
    )
    schedule_date = fields.Datetime(
        "Scheduled Date",
        default=fields.Datetime.now,
        index=True,
        required=True,
        copy=False,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user,
        check_company=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    part_lines = fields.One2many(
        comodel_name="repair.batch.line",
        inverse_name="repair_batch_id",
        string="Parts",
    )

    # END #######
    # METHODS ###

    def _compute_repair_count(self):
        """Helper field compute to show/hide create repairs button."""
        for batch in self:
            batch.repair_count = len(batch.repair_ids)

    @api.depends("picking_type_id")
    def _compute_location_id(self):
        for repair in self:
            repair.location_id = repair.picking_type_id.default_location_src_id

    def action_generate_repairs(self):
        repair_order_model = self.env["repair.order"]
        for batch in self:
            if batch.product_id.tracking == "serial":
                for lot in batch.lot_ids:
                    if not repair_order_model.search(
                        [
                            ("product_id", "=", batch.product_id.id),
                            ("lot_id", "=", lot.id),
                            ("state", "not in", ["done", "cancel"]),
                        ]
                    ):
                        repair_order_model.create(
                            {
                                "product_id": batch.product_id.id,
                                "lot_id": lot.id,
                                "product_qty": 1.0,
                                "ticket_id": batch.ticket_id.id,
                                "repair_batch_id": batch.id,
                                "partner_id": batch.ticket_id.partner_id.id,
                            }
                        )
                    else:
                        continue
            else:
                if not repair_order_model.search(
                    [
                        ("product_id", "=", batch.product_id.id),
                        ("state", "not in", ["done", "cancel"]),
                    ]
                ):
                    repair_order_model.create(
                        {
                            "product_id": batch.product_id.id,
                            "product_qty": batch.qty,
                            "ticket_id": batch.ticket_id.id,
                            "repair_batch_id": batch.id,
                        }
                    )
                else:
                    raise ValidationError(
                        _(
                            """There is already an open repair order for one or more of the products."""
                        )
                    )

            # Ensure moves are created immediately after generating repairs
            batch._propagate_parts_to_repairs()

    @api.model_create_multi
    def create(self, vals_list):
        batches = super().create(vals_list)
        for batch in batches:
            batch._propagate_parts_to_repairs()
        return batches

    def write(self, vals):
        res = super().write(vals)

        for repair in self:
            if "part_lines" in vals:
                repair._propagate_parts_to_repairs()

            if "schedule_date" in vals:
                (repair.move_id + repair.move_ids).filtered(
                    lambda m: m.state not in ("done", "cancel")
                ).write({"date": repair.schedule_date})
        return res

    def _propagate_parts_to_repairs(self):
        """Ensure all open repair orders get the same move_ids linked to batch lines."""
        for batch in self:
            open_repairs = batch.repair_ids.filtered(
                lambda r: r.state not in ["done", "cancel"]
            )

            for part in batch.part_lines:
                for repair in open_repairs:
                    # Find or create a move linked to this repair
                    move = self.env["stock.move"].search(
                        [
                            ("repair_id", "=", repair.id),
                            ("repair_batch_line_id", "=", part.id),
                        ],
                        limit=1,
                    )

                    if move:
                        # Update existing move
                        move.write(
                            {
                                "product_id": part.product_id.id,
                                "product_uom_qty": part.quantity,
                                "repair_line_type": part.repair_line_type,
                            }
                        )
                    else:
                        # Create a new move linked to this repair order and batch line
                        self.env["stock.move"].create(
                            {
                                "repair_id": repair.id,
                                "repair_batch_line_id": part.id,
                                "product_id": part.product_id.id,
                                "product_uom_qty": part.quantity,
                                "repair_line_type": part.repair_line_type,
                            }
                        )

            # Remove any moves from repairs that no longer exist in batch
            batch_product_ids = batch.part_lines.mapped("id")
            for repair in open_repairs:
                repair.move_ids.filtered(
                    lambda m: m.repair_batch_line_id.id not in batch_product_ids
                ).unlink()

    # ACTION BUTTONS

    def action_validate(self):
        """Confirm all related repair orders"""
        warning_actions = []
        for batch in self:
            for repair in batch.repair_ids.filtered(lambda r: r.state == "draft"):
                res = repair.action_validate()
                if isinstance(res, dict) and res.get("type") == "ir.actions.act_window":
                    warning_actions.append(res)

        if warning_actions:
            return warning_actions[
                0
            ]  # Return the first warning (Odoo handles one action at a time)

        self._update_batch_state()

    def action_repair_start(self):
        """Start all related repair orders"""
        for batch in self:
            batch.repair_ids.filtered(
                lambda r: r.state == "confirmed"
            ).action_repair_start()
        batch._update_batch_state()

    def action_repair_end(self):
        """Mark all related repair orders as repaired"""
        for batch in self:
            batch.repair_ids.filtered(
                lambda r: r.state == "under_repair"
            ).action_repair_end()
        batch._update_batch_state()

    def action_repair_done(self):
        """Complete all related repair orders"""
        for batch in self:
            batch.repair_ids.filtered(
                lambda r: r.state == "under_repair"
            ).action_repair_done()
        batch._update_batch_state()

    def action_repair_cancel(self):
        """Cancel all related repair orders"""
        for batch in self:
            batch.repair_ids.filtered(
                lambda r: r.state not in ["done", "cancel"]
            ).action_repair_cancel()
        batch._update_batch_state()

    def action_repair_cancel_draft(self):
        for batch in self:
            batch.repair_ids.filtered(
                lambda r: r.state not in ("cancel", "done")
            ).action_repair_cancel()

            batch.repair_ids.filtered(
                lambda r: r.state in ["cancel"]
            ).action_repair_cancel_draft()
            self.state = "draft"
        batch._update_batch_state()

    def _update_batch_state(self):
        """Update batch state based on repair order states"""
        for batch in self:
            states = batch.repair_ids.mapped("state")

            # Check if any repair orders are confirmed
            if any(s == "draft" for s in states):
                batch.state = "draft"

            # Check if any repair orders are confirmed
            elif any(s == "confirmed" for s in states):
                batch.state = "confirmed"

            # If there is any repair order under repair, set state to 'under_repair'
            elif any(s == "under_repair" for s in states):
                batch.state = "under_repair"

            # If all repair orders are cancelled
            elif all(s == "cancel" for s in states):
                batch.state = "cancel"

            # Check if all repair orders are done and cancelled
            elif all(s in ["cancel", "done"] for s in states):
                batch.state = "done"

            # Default to draft if no specific state is met
            else:
                batch.state = "draft"

    # END #######
