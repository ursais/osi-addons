# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RepairBatch(models.Model):
    _name = "repair.batch"
    _description = "Repair batch"

    @api.model
    def _default_picking_type_id(self):
        return self._get_picking_type().get((self.env.company, self.env.user))

    # COLUMNS ###

    name = fields.Char(
        string="Name",
    )
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
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
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
    lot_ids_domain = fields.Binary(
        string="Serial/Lot Domain",
        help="Dynamic domain used for limiting serial numbers based on product.",
        compute="_compute_lot_ids_domain",
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
    repair_count = fields.Integer(
        string="Repair Count",
        compute="_compute_repair_count",
    )
    sale_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="SO Line",
    )
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
    )
    schedule_date = fields.Datetime(
        string="Scheduled Date",
        default=fields.Datetime.now,
        index=True,
        required=True,
        copy=False,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
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
    unreserve_visible = fields.Boolean(
        string="Unreserve Button Visible",
        compute="_compute_unreserve_visible",
    )
    reserve_visible = fields.Boolean(
        string="Reserve Button Visible",
        compute="_compute_reserve_visible",
    )
    start_repair_visible = fields.Boolean(
        string="Start Repair Button Visible",
        compute="_compute_repair_buttons_visible",
    )
    end_repair_visible = fields.Boolean(
        string="End Repair Button Visible",
        compute="_compute_repair_buttons_visible",
    )
    cancel_visible = fields.Boolean(
        string="Cancel Button Visible",
        compute="_compute_repair_buttons_visible",
    )
    show_create_removal_button = fields.Boolean(
        compute="_compute_show_create_removal_button",
    )

    # END #######
    # METHODS ###

    @api.depends("repair_ids.move_ids")
    def _compute_show_create_removal_button(self):
        for batch in self:
            batch.show_create_removal_button = any(
                not r.move_ids for r in batch.repair_ids
            )

    def open_batch_full_form(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.batch",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.onchange("lot_ids")
    def _onchange_lot_ids(self):
        """Auto-set product, sale order, sale line, and quantity based on selected lots."""
        if not self.lot_ids:
            self.qty = 1
            self.sale_id = False
            self.sale_line_id = False
            return

        # Auto-set product from the first lot if not already set
        first_lot = self.lot_ids[0]
        if not self.product_id:
            self.product_id = first_lot.product_id

        # Determine the real lot record (handles unsaved records)
        real_lot_id = first_lot._origin.id if first_lot._origin else first_lot.id
        lot = self.env["stock.lot"].browse(real_lot_id)

        # Set sale order and attempt to link correct sale line
        if not self.sale_id and lot.sale_order_ids:
            sale_order = lot.sale_order_ids[0]
            self.sale_id = sale_order

            # Look for stock move lines of this order that used this lot
            move_lines = sale_order.picking_ids.move_line_ids.filtered(
                lambda ml: ml.lot_id.id == lot.id
            )
            if (
                move_lines
                and move_lines[0].move_id
                and move_lines[0].move_id.sale_line_id
            ):
                self.sale_line_id = move_lines[0].move_id.sale_line_id
            else:
                # Fallback: use matching product line if no lot-linked line is found
                matching_line = sale_order.order_line.filtered(
                    lambda l: l.product_id == self.product_id
                )
                if matching_line:
                    self.sale_line_id = matching_line[0]

        # Set quantity based on number of selected serials
        self.qty = len(self.lot_ids) or 1

    @api.onchange("sale_id")
    def _onchange_sale_id(self):
        if self.sale_id:
            order = self.sale_id

            # sale_line_id
            if self.sale_line_id and self.sale_line_id.order_id != order:
                self.sale_line_id = False

            # product_id
            valid_product_ids = order.order_line.mapped("product_id")
            if self.product_id and self.product_id not in valid_product_ids:
                self.product_id = False

            # lot_ids
            move_lines = order.picking_ids.move_ids.move_line_ids
            valid_lot_ids = move_lines.mapped("lot_id").filtered(lambda l: l)

            if self.lot_ids:
                still_valid = self.lot_ids & valid_lot_ids
                if still_valid:
                    self.lot_ids = still_valid

            # auto-set partner if not already set
            if not self.partner_id:
                self.partner_id = order.partner_id

        else:
            self.sale_line_id = False

    @api.onchange("sale_line_id")
    def _onchange_sale_line_id(self):
        if self.sale_line_id:
            self.product_id = self.sale_line_id.product_id

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.sale_id and self.product_id:
            sale_products = self.sale_id.order_line.mapped("product_id")
            if self.product_id not in sale_products:
                self.sale_line_id = False  # Or maybe also clear product_id?
                self.lot_ids = False

    @api.depends(
        "product_id",
        "sale_id",
        "sale_line_id",
    )
    def _compute_lot_ids_domain(self):
        """
        Sets the domain of the lot_ids field based on the selected product or sale order.
        This allows a user to initially choose a serial instead of going in on the product side.
        """
        for rec in self:
            domain = []
            if rec.sale_line_id:
                product = rec.sale_line_id.product_id
                pickings = rec.sale_line_id.order_id.picking_ids
                move_lines = pickings.move_ids.move_line_ids.filtered(
                    lambda m: m.product_id == product
                )
                lot_ids = move_lines.mapped("lot_id").filtered(lambda l: l)
                rec.product_id = product.id

                domain = [("id", "in", lot_ids.ids), ("product_id", "=", product.id)]
            elif rec.sale_id:
                # Get all stock.lot IDs linked to stock.move lines of the sale order
                move_lines = rec.sale_id.picking_ids.move_ids.move_line_ids
                lot_ids = move_lines.mapped("lot_id").filtered(lambda l: l)
                # raise ValidationError(move_lines)
                if rec.product_id:
                    domain = [
                        ("id", "in", lot_ids.ids),
                        ("product_id", "=", rec.product_id.id),
                    ]
                else:
                    domain = [("id", "in", lot_ids.ids)]
            elif rec.product_id:
                domain = [("product_id", "=", rec.product_id.id)]
            rec.lot_ids_domain = domain

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
                # Validation: Ensure number of serial numbers matches quantity
                if len(batch.lot_ids) != batch.qty:
                    raise ValidationError(
                        _(
                            "%s: The number of serial numbers (%d) does not match the quantity (%d) for product %s."
                        )
                        % (
                            batch.name,
                            len(batch.lot_ids),
                            batch.qty,
                            batch.product_id.default_code,
                        )
                    )

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
                                "partner_id": batch.partner_id.id,
                                "schedule_date": batch.schedule_date,
                            }
                        )
                    else:
                        continue
            else:
                repair_orders = repair_order_model.search(
                    [
                        ("product_id", "=", batch.product_id.id),
                        ("state", "not in", ["done", "cancel"]),
                        ("partner_id", "=", batch.ticket_id.partner_id.id),
                    ]
                )

                if not repair_orders:
                    repair_order_model.create(
                        {
                            "partner_id": batch.partner_id.id,
                            "product_id": batch.product_id.id,
                            "product_qty": batch.qty,
                            "ticket_id": batch.ticket_id.id,
                            "repair_batch_id": batch.id,
                        }
                    )
                else:
                    repair_order_names = ", ".join(repair_orders.mapped("name"))
                    raise ValidationError(
                        _(
                            """There is already an open repair order for one or more of the products: %s"""
                        )
                        % repair_order_names
                    )

            # Ensure moves are created immediately after generating repairs
            batch._propagate_parts_to_repairs()

    def action_batch_create_removal_lines(self):
        for batch in self:
            repairs = batch.repair_ids
            repairs_to_process = repairs.filtered(lambda r: not r.move_ids)

            # Step 1: Call existing logic to generate stock.move lines
            for repair in repairs_to_process:
                repair.action_create_removal_lines()

            # Step 2: Index move_ids from all repairs in the batch
            all_moves = repairs.mapped("move_ids").filtered(
                lambda m: m.repair_line_type == "remove"
            )

            # Group by (product_id, repair_line_type)
            move_groups = {}
            for move in all_moves:
                key = (move.product_id.id, move.repair_line_type)
                move_groups.setdefault(key, []).append(move)

            # Step 3: Create batch lines for common components
            for key, group_moves in move_groups.items():
                product_id, line_type = key
                repairs_with_this_move = set(move.repair_id.id for move in group_moves)
                if set(repairs.ids) == repairs_with_this_move:
                    total_qty = sum(move.product_uom_qty for move in group_moves)

                    batch_line = self.env["repair.batch.line"].create(
                        {
                            "repair_batch_id": batch.id,
                            "product_id": product_id,
                            "repair_line_type": line_type,
                            "quantity": total_qty,
                        }
                    )

                    self.env["stock.move"].browse([m.id for m in group_moves]).write(
                        {"repair_batch_line_id": batch_line.id}
                    )

    def _update_ticket_sale_ids(self, old_sale_ids=None):
        """
        Helper method:
        Ensure ticket.original_sale_order_ids correctly reflects the batches linked to it.

        :param old_sale_ids: dict mapping batch.id -> old sale_id before write (optional)
        """
        for batch in self:
            ticket = batch.ticket_id
            new_sale = batch.sale_id
            new_sale_id = new_sale.id if new_sale else None
            old_sale_id = old_sale_ids.get(batch.id) if old_sale_ids else None

            # Add new sale_id to ticket if not already present
            if new_sale and new_sale_id not in ticket.original_sale_order_ids.ids:
                ticket.original_sale_order_ids = [(4, new_sale_id)]
                if not ticket.partner_id:
                    ticket.partner_id = new_sale.partner_id

            # Remove old sale_id if changed and no other batch references it
            if old_sale_id and old_sale_id != new_sale_id:
                other_batches = self.search(
                    [
                        ("ticket_id", "=", ticket.id),
                        ("sale_id", "=", old_sale_id),
                        ("id", "!=", batch.id),
                    ]
                )
                if not other_batches:
                    ticket.original_sale_order_ids = [(3, old_sale_id)]

    @api.model_create_multi
    def create(self, vals_list):
        batches = super().create(vals_list)
        for batch in batches:
            batch.name = self.env["ir.sequence"].next_by_code("repair.batch") or "New"
            batch._propagate_parts_to_repairs()

        batches._update_ticket_sale_ids()

        return batches

    def write(self, vals):
        old_sale_ids = {batch.id: batch.sale_id.id for batch in self if batch.sale_id}
        res = super().write(vals)

        self._update_ticket_sale_ids(old_sale_ids)
        for batch in self:
            if "part_lines" in vals:
                batch._propagate_parts_to_repairs()
            if "schedule_date" in vals:
                (batch.move_id + batch.move_ids).filtered(
                    lambda m: m.state not in ("done", "cancel")
                ).write({"date": batch.schedule_date})
        return res

    def unlink(self):
        # Gather all necessary info before deletion
        sale_ticket_map = [
            (batch.sale_id.id if batch.sale_id else None, batch.ticket_id.id)
            for batch in self
        ]

        res = super().unlink()

        # After deletion, update tickets
        for sale_id, ticket_id in sale_ticket_map:
            if not sale_id:
                continue
            ticket = self.env["helpdesk.ticket"].browse(ticket_id)
            # Check if any remaining batch still references this sale
            other_batches = self.search(
                [
                    ("ticket_id", "=", ticket.id),
                    ("sale_id", "=", sale_id),
                ]
            )
            if not other_batches:
                ticket.original_sale_order_ids = [(3, sale_id)]
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
                                "reason_code_id": part.reason_code_id.id,
                                "note": part.note,
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
                                "reason_code_id": part.reason_code_id.id,
                                "note": part.note,
                            }
                        )

            # Remove any moves from repairs that no longer exist in batch
            batch_product_ids = batch.part_lines.mapped("id")
            for repair in open_repairs:
                repair.move_ids.filtered(
                    lambda m: m.repair_batch_line_id.id not in batch_product_ids
                ).unlink()

    # ACTION BUTTONS

    @api.depends("repair_ids.unreserve_visible")
    def _compute_unreserve_visible(self):
        for batch in self:
            batch.unreserve_visible = any(batch.repair_ids.mapped("unreserve_visible"))

    @api.depends("repair_ids.reserve_visible")
    def _compute_reserve_visible(self):
        for batch in self:
            batch.reserve_visible = any(batch.repair_ids.mapped("reserve_visible"))

    @api.depends("repair_ids.state")
    def _compute_repair_buttons_visible(self):
        for batch in self:
            batch.start_repair_visible = any(
                repair.state == "confirmed" for repair in batch.repair_ids
            )
            batch.end_repair_visible = any(
                repair.state in ("under_repair") for repair in batch.repair_ids
            )
            batch.cancel_visible = any(
                repair.state in ("confirmed", "under_repair")
                for repair in batch.repair_ids
            )

    def action_assign(self):
        for batch in self:
            for repair in batch.repair_ids:
                repair.move_ids._action_assign()

    def action_unreserve(self):
        for batch in self:
            for repair in batch.repair_ids:
                repair.move_ids.filtered(
                    lambda m: m.state in ("assigned", "partially_available")
                )._do_unreserve()

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

    @api.constrains("sale_id", "product_id", "sale_line_id", "lot_ids")
    def _check_sale_and_product_consistency(self):
        for rec in self:
            if rec.sale_id:
                sale_products = rec.sale_id.order_line.mapped("product_id")
                if rec.product_id and rec.product_id not in sale_products:
                    raise ValidationError(
                        _("Product %s is not part of the selected sale order.")
                        % rec.product_id.display_name
                    )

                if rec.lot_ids:
                    # Get valid lots from the picking linked to this sale
                    valid_lots = rec.sale_id.picking_ids.move_ids.move_line_ids.mapped(
                        "lot_id"
                    )
                    invalid_lots = rec.lot_ids - valid_lots
                    if invalid_lots:
                        raise ValidationError(
                            _(
                                "Some selected serial numbers are not part of the sale order: %s"
                            )
                            % ", ".join(invalid_lots.mapped("name"))
                        )

            if (
                rec.sale_line_id
                and rec.product_id
                and rec.sale_line_id.product_id != rec.product_id
            ):
                raise ValidationError(
                    _("Sale Order Line product does not match selected product.")
                )

            if rec.sale_line_id and rec.sale_line_id.order_id != rec.sale_id:
                raise ValidationError(
                    _("Sale line is not part of the selected Sale Order.")
                )

    # END #######
