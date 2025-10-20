# Import Odoo libs
from datetime import timedelta

# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    """Inherit helpdesk tickets to add batch repairs."""

    _inherit = "helpdesk.ticket"

    # COLUMNS ###

    repair_batch_ids = fields.One2many(
        comodel_name="repair.batch",
        inverse_name="ticket_id",
        string="Repair Batch",
    )
    repair_sale_order_ids = fields.One2many(
        comodel_name="sale.order",
        inverse_name="helpdesk_ticket_id",
        string="Repair Sale Orders",
        help="New Sale Orders generated from this ticket.",
    )
    original_sale_order_ids = fields.Many2many(
        comodel_name="sale.order",
        string="Original Sale Orders",
        readonly=True,
        help="Original Sale Orders where the systems were originally sold, populated by the Import from Sale Order wizard.",
    )
    repair_sale_order_count = fields.Integer(
        string="Sale Order(s)",
        compute="_compute_button_counts",
    )
    out_transfer_count = fields.Integer(
        string="OUT(s)",
        compute="_compute_button_counts",
        help="Counts the number of OUT transfers",
    )
    in_transfer_count = fields.Integer(
        string="IN(s)",
        compute="_compute_button_counts",
        help="Counts the number of IN transfers",
    )
    show_generate_repairs = fields.Boolean(
        string="Show Generate Repairs Button",
        compute="_compute_show_generate_repairs",
        help="Helper field used by the visibility attribute of the button.",
    )
    refund_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="helpdesk_ticket_id",
        string="Refunds",
        help="Refunds Issued from this helpdesk ticket.",
    )
    out_refund_count = fields.Integer(
        string="Refund(s)",
        compute="_compute_button_counts",
        help="Counts the number of Refunds",
    )
    repair_history_html = fields.Html(
        compute="_compute_repair_history_html",
        sanitize=True,
        help="Field used within the alert message where other repairs are found.",
    )
    show_repair_history_alert = fields.Boolean(
        compute="_compute_repair_history_html",
        help="Helper field used for the alert invisible attribute.",
    )
    account_manager_id = fields.Many2one(
        comodel_name="res.users",
        string="Account Manager",
        related="partner_id.account_manager_id",
        store=True,
    )
    flags = fields.Char(string="Flags")
    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Shipping Method",
    )
    shipping_account = fields.Char(string="Shipping Account")

    # END #######
    # METHODS ###

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        team_id = vals.get("team_id")
        if team_id:
            team = self.env["helpdesk.team"].browse(team_id)
            if team.sequence_id:
                vals["name"] = (
                    "Auto-generated"  # Placeholder before actual sequence is assigned
                )
        return vals

    @api.depends(
        "repair_ids",
        "repair_ids.lot_id",
        "repair_ids.schedule_date",
    )
    def _compute_repair_history_html(self):
        state_labels = dict(
            self.env["repair.order"]._fields["state"]._description_selection(self.env)
        )
        for ticket in self:
            messages = []
            # Collect all lot_ids and repair ids on the ticket
            ticket_lot_ids = ticket.repair_ids.mapped("lot_id")
            ticket_repair_ids = ticket.repair_ids.ids

            for lot in ticket_lot_ids:
                # Find historical repairs for this lot excluding ticket repairs
                history = self.env["repair.order"].search(
                    [
                        ("lot_id", "=", lot.id),
                        ("id", "not in", ticket_repair_ids),
                    ]
                )
                if history:
                    hist_links = "".join(
                        f'<li><a href="/web#id={h.id}&model=repair.order&view_type=form">{h.name}</a>'
                        f" — {state_labels.get(h.state, h.state)}"
                        f' ({h.schedule_date.date() if h.schedule_date else ""})'
                        f"</li>"
                        for h in history
                    )
                    messages.append(
                        f"<strong>Serial: {lot.name}</strong><ul>{hist_links}</ul>"
                    )
            ticket.show_repair_history_alert = bool(messages)
            ticket.repair_history_html = "".join(messages) if messages else ""

    def _compute_button_counts(self):
        for ticket in self:
            ticket.repair_sale_order_count = len(ticket.repair_sale_order_ids)
            ticket.out_transfer_count = len(
                ticket.repair_sale_order_ids.mapped("picking_ids")
            )
            ticket.in_transfer_count = len(
                self.env["stock.picking"].search([("ticket_id", "=", self.id)])
            )
            ticket.out_refund_count = len(
                self.env["account.move"].search(
                    [
                        ("helpdesk_ticket_id", "=", self.id),
                        ("move_type", "=", "out_refund"),
                    ]
                )
            )

    def action_view_repair_sale_orders(self):
        self.ensure_one()
        action = {
            "res_model": "sale.order",
            "type": "ir.actions.act_window",
        }
        if len(self.repair_sale_order_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.repair_sale_order_ids[0].id,
                }
            )
        else:
            action.update(
                {
                    "name": _("Repair Sale Orders %s", self.name),
                    "domain": [("id", "in", self.repair_sale_order_ids.ids)],
                    "view_mode": "tree,form",
                }
            )
        return action

    def action_view_out_transfers(self):
        """View outbound transfers related to sale order deliveries."""
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        transfers = self.repair_sale_order_ids.mapped("picking_ids")

        if len(transfers) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": transfers.id,
                    "views": [(self.env.ref("stock.view_picking_form").id, "form")],
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", transfers.ids)],
                    "view_mode": "tree,form",
                    "views": [
                        (self.env.ref("stock.vpicktree").id, "tree"),
                        (self.env.ref("stock.view_picking_form").id, "form"),
                    ],
                }
            )

        return action

    def action_view_in_transfers(self):
        """View inbound transfers (receipts) related to this ticket."""
        action = self.env.ref("stock.action_picking_tree_incoming").read()[0]
        transfers = self.env["stock.picking"].search(
            [
                ("ticket_id", "=", self.id),
                ("picking_type_code", "=", "incoming"),
            ]
        )

        if len(transfers) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": transfers.id,
                    "views": [(self.env.ref("stock.view_picking_form").id, "form")],
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", transfers.ids)],
                    "view_mode": "tree,form",
                    "views": [
                        (self.env.ref("stock.vpicktree").id, "tree"),
                        (self.env.ref("stock.view_picking_form").id, "form"),
                    ],
                }
            )

        return action

    def action_view_refund_ids(self):
        self.ensure_one()
        action = {
            "res_model": "account.move",
            "type": "ir.actions.act_window",
        }
        if len(self.refund_ids) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": self.refund_ids[0].id,
                }
            )
        else:
            action.update(
                {
                    "name": _("Refunds %s", self.name),
                    "domain": [("id", "in", self.refund_ids.ids)],
                    "view_mode": "tree,form",
                }
            )
        return action

    @api.depends(
        "repair_batch_ids.repair_count",
        "repair_batch_ids.qty",
    )
    def _compute_show_generate_repairs(self):
        for ticket in self:
            ticket.show_generate_repairs = any(
                batch.repair_count < batch.qty for batch in ticket.repair_batch_ids
            )

    def action_generate_repairs(self):
        """Runs `action_generate_repairs` on all batches where the button is visible."""
        batches_to_process = self.repair_batch_ids.filtered(
            lambda batch: batch.repair_count < batch.qty
            and batch.state not in ("done", "cancel")
        )
        if not batches_to_process:
            raise ValidationError(_("No batches require repair generation."))

        for batch in batches_to_process:
            batch.action_generate_repairs()

    def action_create_receipt(self):
        stock_picking_obj = self.env["stock.picking"]
        stock_move_obj = self.env["stock.move"]
        stock_move_line_obj = self.env["stock.move.line"]

        if not self.repair_batch_ids:
            raise ValidationError("No repair batches linked to this ticket.")

        product_quantities = {}  # {product_id: {"qty": total_qty, "lots": []}}

        # Set source as Customer Virtual Location
        customer_location = self.env["stock.location"].search(
            [("usage", "=", "customer")], limit=1
        )
        if not customer_location:
            raise ValidationError("Customer virtual location not found.")

        source_location_id = customer_location.id

        # Collect repair locations
        repair_locations = {
            repair.location_id.id
            for batch in self.repair_batch_ids
            for repair in batch.repair_ids
        }
        if len(repair_locations) > 1:
            raise ValidationError(
                "Multiple repair locations found. Ensure all repairs use the same location."
            )

        destination_location_id = repair_locations.pop() if repair_locations else False
        if not destination_location_id:
            raise ValidationError(
                "Could not determine the repair destination location."
            )

        for batch in self.repair_batch_ids:
            for repair in batch.repair_ids.filtered(
                lambda r: r.state not in ("done", "under_repair", "cancel")
            ):
                product_id = repair.product_id.id
                lot_id = (
                    repair.lot_id.id if repair.lot_id else False
                )  # Use lot_id from repair

                if product_id not in product_quantities:
                    product_quantities[product_id] = {"qty": 0, "lots": []}

                product_quantities[product_id]["qty"] += repair.product_qty

                if lot_id:
                    product_quantities[product_id]["lots"].append(
                        (
                            0,
                            0,
                            {
                                "lot_id": lot_id,
                                "qty_done": repair.product_qty,
                            },
                        )
                    )

        if not product_quantities:
            raise ValidationError("No valid products found to create a receipt.")

        # Get the RMA Repairs IN Pick Type from the Warehouse
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )

        if not warehouse or not warehouse.rma_repair_in_type_id:
            raise ValidationError(
                "RMA Repairs Incoming Picking Type is not configured for the current warehouse. "
                "Please set 'Repair Incoming Picking Type' on the warehouse."
            )

        picking_type = warehouse.rma_repair_in_type_id

        receipt = stock_picking_obj.create(
            {
                "partner_id": self.partner_id.id,
                "origin": self.name,
                "picking_type_id": picking_type.id,
                "location_id": source_location_id,
                "location_dest_id": destination_location_id,
                "ticket_id": self.id,
                "owner_id": self.partner_id.id or False,
                "scheduled_date": fields.Datetime.now() + timedelta(days=7),
            }
        )

        for product_id, data in product_quantities.items():
            product = self.env["product.product"].browse(product_id)
            stock_move = stock_move_obj.create(
                {
                    "picking_id": receipt.id,
                    "product_id": product_id,
                    "name": product.display_name,
                    "product_uom": product.uom_id.id,
                    "product_uom_qty": data["qty"],
                    "location_id": source_location_id,
                    "location_dest_id": destination_location_id,
                    "date": fields.Datetime.now() + timedelta(days=7),
                }
            )

            # Create stock move lines with lot tracking
            for lot in data["lots"]:
                lot_data = lot[2]  # Lot data dictionary

                # Ensure product_id and lot_id are correctly set in the move line
                lot_data["move_id"] = stock_move.id
                lot_data["product_id"] = stock_move.product_id.id
                lot_data["location_id"] = source_location_id
                lot_data["location_dest_id"] = destination_location_id

                # Fetch the lot record using lot_id (if lot_id is an integer ID)
                lot_record = self.env["stock.lot"].browse(lot_data["lot_id"])

                # Ensure lot_record is valid
                if not lot_record.exists():
                    raise ValidationError(
                        f"Lot ID {lot_data['lot_id']} does not exist."
                    )

                # Ensure product_id is consistent between the lot and the product being moved
                if lot_record.product_id != stock_move.product_id:
                    raise ValidationError(
                        f"Lot {lot_record.name} is incompatible with product {stock_move.product_id.name}"
                    )

                # Assign the product_id to the move line (in case it's missing from lot_data)
                lot_data["lot_id"] = lot_record.id

                # Create the stock move line
                stock_move_line_obj.create(lot_data)

        return {
            "name": "Receipt Transfer",
            "type": "ir.actions.act_window",
            "res_model": "stock.picking",
            "view_mode": "form",
            "res_id": receipt.id,
        }

    def action_create_sale_order(self):
        sale_order_obj = self.env["sale.order"]
        sale_order_line_obj = self.env["sale.order.line"]

        repair_orders = self.repair_batch_ids.mapped("repair_ids").filtered(
            lambda r: not r.sale_order_id or r.sale_order_id.state == "cancel"
        )

        product_quantities = {}
        move_repair_map = {}
        repair_product_map = {}

        if repair_orders:
            for repair in repair_orders:
                # logic for the repaired device itself
                if repair.product_id:
                    pid = repair.product_id.id
                    repair_product_map[pid] = (
                        repair_product_map.get(pid, 0) + repair.product_qty
                    )

                # logic for added components, grouped by under_warranty
                for move in repair.move_ids.filtered(
                    lambda m: m.repair_line_type == "add"
                ):
                    pid = move.product_id.id
                    uw = bool(repair.under_warranty)
                    key = (pid, uw)
                    # sum up quantities
                    product_quantities[key] = (
                        product_quantities.get(key, 0.0) + move.product_uom_qty
                    )
                    # remember which move/repair pair goes to which grouping
                    move_repair_map.setdefault(key, []).append((move, repair))

        # merge in repaired‐device qtys (these always ship, price = 0)
        for pid, qty in repair_product_map.items():
            key = (pid, False)  # price=0 & ship back
            product_quantities[key] = product_quantities.get(key, 0.0) + qty

        # Check to make sure the RMA Return order type exists
        so_type = self.env.ref("ol_helpdesk_repair_batch.rma_return_sale_type", False)
        if not so_type:
            raise ValidationError(
                "The 'RMA Return' sale order type is missing. Please see your administrator."
            )

        # Try to get current user's sales team
        team_id = self.env.user.sale_team_id.id if self.env.user.sale_team_id else None

        sale_order = sale_order_obj.create(
            {
                "partner_id": self.partner_id.id,
                "origin": self.name,
                "to_send_confirmation_email": False,
                "type_id": so_type.id,
                "team_id": team_id,
                "user_id": self.env.user.id,
            }
        )

        # create lines
        sale_line_map = {}
        for (product_id, under_warranty), qty in product_quantities.items():
            product = self.env["product.product"].browse(product_id)
            # determine price and shipment flag
            if (product_id in repair_product_map) and not under_warranty:
                # original repaired device
                price = 0.0
                is_component = False  # we want to ship it back
            else:
                # component: under warranty => free; otherwise list price
                price = 0.0 if under_warranty else product.list_price
                is_component = True  # we don't want to ship it back

            line = sale_order_line_obj.create(
                {
                    "order_id": sale_order.id,
                    "product_id": product_id,
                    "product_uom_qty": qty,
                    "product_uom": product.uom_id.id,
                    "price_unit": price,
                    "is_repair_component": is_component,
                    "repair_ids": [
                        (
                            6,
                            0,
                            [
                                r.id
                                for r in self.repair_batch_ids.mapped("repair_ids")
                                if r.product_id.id == product_id
                            ],
                        )
                    ],
                }
            )
            sale_line_map[(pid, under_warranty)] = line.id

        # link back to repairs/moves
        for key, pairs in move_repair_map.items():
            line_id = sale_line_map.get(key)
            for move, repair in pairs:
                # Always relink if not linked, or if linked SO is canceled
                if not repair.sale_order_id or repair.sale_order_id.state == "cancel":
                    repair.sale_order_id = sale_order.id
                move.sale_line_id = line_id

        self.repair_sale_order_ids = [(6, 0, [sale_order.id])]

        return {
            "name": "Sale Order",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": sale_order.id,
        }

    def action_open_credit_note_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Create Refund",
            "res_model": "repair.credit.note.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_ticket_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            team_id = vals.get("team_id")
            if team_id:
                team = self.env["helpdesk.team"].browse(team_id)
                if team.sequence_id:
                    vals["name"] = team.sequence_id.next_by_id()
        return super().create(vals_list)
