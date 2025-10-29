# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    # COLUMNS ###

    repair_batch_id = fields.Many2one(
        comodel_name="repair.batch",
        string="Repair Batch",
        ondelete="set null",
    )
    part_lines = fields.One2many(
        comodel_name="repair.batch.line",
        inverse_name="repair_batch_id",
        string="Parts",
    )
    show_create_removal_button = fields.Boolean(
        compute="_compute_show_create_removal_button",
    )
    scrap_ids = fields.One2many(
        comodel_name="stock.scrap",
        inverse_name="repair_id",
        string="Scrap Records",
    )
    scrap_count = fields.Integer(
        compute="_compute_scrap_count",
        string="Scrap Orders",
    )
    external_notes = fields.Text(string="Customer Notes")
    history_repair_ids = fields.Many2many(
        comodel_name="repair.order",
        compute="_compute_history_fields",
        string="Historical Repairs",
        help="Computed field to show other repairs for the same serial.",
    )
    history_repair_html = fields.Html(
        compute="_compute_history_fields",
        sanitize=True,
        help="Field used within the alert message where other repairs are found.",
    )
    show_repair_history_alert = fields.Boolean(
        compute="_compute_history_fields",
        help="Helper field used for the alert invisible attribute.",
    )
    picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="repair_id",
        string="Internal Transfers",
        readonly=True,
        copy=False,
    )
    picking_count = fields.Integer(
        string="Internal Transfers",
        compute="_compute_picking_count",
    )

    # END #######
    # METHODS ###

    @api.depends("scrap_ids")
    def _compute_scrap_count(self):
        for rec in self:
            rec.scrap_count = len(rec.scrap_ids)

    @api.depends("move_ids")
    def _compute_show_create_removal_button(self):
        for rec in self:
            rec.show_create_removal_button = not rec.move_ids

    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        action["domain"] = [("id", "in", self.picking_ids.ids)]
        action["context"] = {"default_repair_id": self.id}
        return action

    @api.depends("lot_id")
    def _compute_history_fields(self):
        state_labels = dict(self._fields["state"]._description_selection(self.env))
        for repair in self:
            if repair.lot_id and repair.id and isinstance(repair.id, int):
                history = self.search(
                    [
                        ("lot_id", "=", repair.lot_id.id),
                        ("id", "!=", repair.id),
                    ]
                )
                repair.history_repair_ids = history
                repair.show_repair_history_alert = bool(history)

                if history:
                    links = "".join(
                        f"<li>"
                        f'<a href="/web#id={h.id}&model=repair.order&view_type=form">{h.name}</a>'
                        f" — {state_labels.get(h.state, h.state)}"
                        f' ({h.schedule_date.date() if h.schedule_date else ""})'
                        f"</li>"
                        for h in history
                    )
                    repair.history_repair_html = f"<ul>{links}</ul>"
                else:
                    repair.history_repair_html = ""
            else:
                repair.history_repair_ids = False
                repair.show_repair_history_alert = False
                repair.history_repair_html = ""

    def open_repair_full_form(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "repair.order",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def _action_repair_confirm(self):
        """
        This is called with confirm wizard when qty is less than zero.
        We want to trigger the _update_batch_state after
        """
        res = super()._action_repair_confirm()
        if self.repair_batch_id:
            self.repair_batch_id._update_batch_state()
        return res

    def action_repair_done(self):
        # Raise validation error if there are remove lines missing reason and note
        for repair in self:
            for line in repair.move_ids:
                if line.repair_line_type == "remove" and line.quantity > 0:
                    if not line.reason_code_id or not line.note:
                        raise ValidationError(
                            _(
                                f"Repair Order {repair.name}: Scrap Reason Code and Line Note are required for remove lines."
                            )
                        )

        # Now run original repair done
        res = super().action_repair_done()

        # Create scrap records for all remove lines
        for repair in self:
            for line in repair.move_ids:
                if line.repair_line_type == "remove" and line.quantity > 0:
                    scrap_vals = {
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom.id,
                        "origin": repair.name,
                        "reason_code_id": line.reason_code_id.id,
                        "note": line.note,
                        "company_id": repair.company_id.id,
                        "scrap_qty": line.quantity,
                        "repair_id": repair.id,
                        "move_ids": [(6, 0, [line.id])],
                        "location_id": line.location_id.id,
                        "scrap_location_id": line.location_dest_id.id,
                    }
                    if line.lot_ids:
                        scrap_vals["lot_ids"] = line.lot_ids.ids
                    scrap = self.env["stock.scrap"].create(scrap_vals)
                    scrap.action_validate()
        return res

    def action_create_removal_lines(self):
        self.ensure_one()
        if not self.lot_id:
            raise ValidationError(_("Please set a Serial Number on this repair order."))

        if self.move_ids:
            return True

        ComponentHistory = self.env["component.history"]

        history_lines = ComponentHistory.search(
            [
                ("lot_id", "=", self.lot_id.id),
                ("invisible", "=", False),
            ]
        )

        new_moves = []
        for history in history_lines:
            new_moves.append(
                (
                    0,
                    0,
                    {
                        "repair_line_type": "remove",
                        "product_id": history.product_id.id,
                        "lot_ids": (
                            history.component_lot_ids.ids
                            if history.component_lot_ids
                            else False
                        ),
                        "product_uom_qty": history.qty_changed,
                        "repair_id": self.id,
                        "location_id": self.location_id.id,
                        "location_dest_id": self.parts_location_id.id,
                    },
                )
            )

        if new_moves:
            self.write({"move_ids": new_moves})

    def action_repair_start(self):
        res = super().action_repair_start()
        for repair in self:
            repair._create_or_update_internal_transfer()
        return res

    def _get_open_picking(self):
        """Return the most recent picking that is not done/cancelled."""
        self.ensure_one()
        return (
            self.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))
            or False
        )

    def _create_or_update_internal_transfer(self):
        """Create or update internal transfers for 'add' moves, including deltas after done transfers."""
        for repair in self:
            add_moves = repair.move_ids.filtered(
                lambda m: m.repair_line_type == "add" and m.product_id.type == "product"
            )
            if not add_moves:
                continue

            # Find warehouse
            warehouse = (
                self.env["stock.warehouse"].search(
                    [
                        ("view_location_id", "parent_of", repair.location_id.id),
                        ("company_id", "=", repair.company_id.id),
                    ],
                    limit=1,
                )
                or repair.company_id.warehouse_id
            )
            picking_type = warehouse.int_type_id
            if not picking_type:
                raise UserError(
                    _("No internal picking type found for warehouse %s.")
                    % warehouse.display_name
                )

            src_loc = picking_type.default_location_src_id or warehouse.lot_stock_id
            dest_loc = repair.location_id

            # Compute product quantities already delivered (done pickings)
            done_moves = repair.picking_ids.filtered(
                lambda p: p.state == "done"
            ).mapped("move_ids")
            delivered = {}
            for m in done_moves:
                delivered[m.product_id.id] = (
                    delivered.get(m.product_id.id, 0.0) + m.product_uom_qty
                )

            # Compute desired totals based on repair add moves
            desired = {}
            for m in add_moves:
                desired[m.product_id.id] = (
                    desired.get(m.product_id.id, 0.0) + m.product_uom_qty
                )

            # Compute remaining delta per product
            deltas = {}
            for pid, total in desired.items():
                already = delivered.get(pid, 0.0)
                if total > already:  # only if more needed
                    deltas[pid] = total - already

            if not deltas:
                continue  # nothing new needed

            # Find or create open picking
            picking = repair.picking_ids.filtered(
                lambda p: p.state not in ("done", "cancel")
            )
            if not picking:
                picking = self.env["stock.picking"].create(
                    {
                        "partner_id": repair.partner_id.id,
                        "picking_type_id": picking_type.id,
                        "location_id": src_loc.id,
                        "location_dest_id": dest_loc.id,
                        "origin": repair.name,
                        "company_id": repair.company_id.id,
                        "repair_id": repair.id,
                    }
                )

            # Sync only the delta quantities
            repair._sync_add_deltas_to_picking(picking, deltas)

            # Confirm & assign
            picking.action_confirm()
            picking.action_assign()

    def _sync_add_deltas_to_picking(self, picking, deltas):
        """Ensure the open picking has moves for the required delta quantities."""
        Move = self.env["stock.move"]
        existing = picking.move_ids.filtered(
            lambda m: m.state not in ("done", "cancel")
        )

        # Update or create moves for each product delta
        for product_id, qty_needed in deltas.items():
            move = existing.filtered(lambda m: m.product_id.id == product_id)
            if move:
                move.product_uom_qty = qty_needed
            else:
                product = self.env["product.product"].browse(product_id)
                Move.create(
                    {
                        "name": picking.name or picking.origin,
                        "product_id": product_id,
                        "product_uom_qty": qty_needed,
                        "product_uom": product.uom_id.id,
                        "location_id": picking.location_id.id,
                        "location_dest_id": picking.location_dest_id.id,
                        "picking_id": picking.id,
                        "company_id": picking.company_id.id,
                        "origin": picking.origin,
                    }
                )

        # Remove any obsolete moves (not in deltas)
        obsolete = existing.filtered(lambda m: m.product_id.id not in deltas)
        obsolete.unlink()

    def write(self, vals):
        """
        If the repair state is changing we want to make sure the batch
        state is also updated.
        """
        res = super().write(vals)

        # Check if the state is changing
        if "state" in vals:
            for order in self:
                if order.repair_batch_id:
                    # Trigger the _update_batch_state method on the batch
                    order.repair_batch_id._update_batch_state()
        # Create/Update internal transfers
        if "move_ids" in vals:
            for repair in self:
                if repair.state == "under_repair":
                    repair._create_or_update_internal_transfer()
        return res

    # END #######
