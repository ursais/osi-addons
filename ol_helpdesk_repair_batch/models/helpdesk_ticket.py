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
    picking_count = fields.Integer(
        string="Internal Transfers",
        compute="_compute_button_counts",
        help="Counts the number of Internal transfers",
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
            ticket.picking_count = len(self.repair_ids.picking_ids.ids)
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

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        action["domain"] = [("id", "in", self.repair_ids.picking_ids.ids)]
        action["context"] = {"default_repair_id": self.id}
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
        SaleOrder = self.env["sale.order"]
        SaleOrderLine = self.env["sale.order.line"]
        StockMove = self.env["stock.move"]
        StockPicking = self.env["stock.picking"]

        # Step 1: Find repairs needing processing
        repair_orders = self.repair_batch_ids.mapped("repair_ids").filtered(
            lambda r: not r.sale_order_id or r.sale_order_id.state == "cancel"
        )
        if not repair_orders:
            return

        # Step 2: Find or create draft SO
        existing_so = self.repair_sale_order_ids.filtered(lambda s: s.state == "draft")[
            :1
        ]
        if existing_so:
            sale_order = existing_so
        else:
            so_type = self.env.ref(
                "ol_helpdesk_repair_batch.rma_return_sale_type", raise_if_not_found=True
            )
            team_id = (
                self.env.user.sale_team_id.id if self.env.user.sale_team_id else None
            )
            sale_order = SaleOrder.create(
                {
                    "partner_id": self.partner_id.id,
                    "origin": self.name,
                    "to_send_confirmation_email": False,
                    "type_id": so_type.id,
                    "team_id": team_id,
                    "user_id": self.env.user.id,
                }
            )
            # Link new SO to batch
            self.repair_sale_order_ids = [(4, sale_order.id)]

        # Step 3: Track already processed repairs
        processed_repairs = sale_order.order_line.mapped("repair_ids").ids

        # Step 4: Build product mapping
        product_quantities = {}  # key -> (product_id, is_component, under_warranty)
        move_repair_map = {}  # key -> list of (move or None, repair)

        for repair in repair_orders:
            if repair.id in processed_repairs:
                continue

            # Main repaired product
            if repair.product_id:
                key = (repair.product_id.id, False, False)
                product_quantities[key] = (
                    product_quantities.get(key, 0.0) + repair.product_qty
                )
                move_repair_map.setdefault(key, []).append((None, repair))

            # Components
            for move in repair.move_ids.filtered(lambda m: m.repair_line_type == "add"):
                key = (move.product_id.id, True, bool(repair.under_warranty))
                product_quantities[key] = (
                    product_quantities.get(key, 0.0) + move.product_uom_qty
                )
                move_repair_map.setdefault(key, []).append((move, repair))

        # Step 5: Merge with existing sale lines or create new
        sale_line_map = {}
        for key, qty in product_quantities.items():
            pid, is_component, under_warranty = key
            product = self.env["product.product"].browse(pid)

            # Determine price
            if not is_component and not under_warranty:
                price = 0.0
            else:
                price = 0.0 if under_warranty else product.list_price

            # Reuse existing line if present
            existing_line = sale_order.order_line.filtered(
                lambda l: l.product_id.id == pid
                and l.is_repair_component == is_component
            )
            if existing_line:
                # Add quantity for new repairs
                existing_line.product_uom_qty += qty
                new_repairs = [
                    r.id
                    for _, r in move_repair_map[key]
                    if r.id not in existing_line.repair_ids.ids
                ]
                if new_repairs:
                    existing_line.repair_ids = [(4, rid) for rid in new_repairs]
                sale_line = existing_line
            else:
                sale_line = SaleOrderLine.create(
                    {
                        "order_id": sale_order.id,
                        "product_id": pid,
                        "product_uom_qty": qty,
                        "product_uom": product.uom_id.id,
                        "price_unit": price,
                        "is_repair_component": is_component,
                        "repair_ids": [(6, 0, [r.id for _, r in move_repair_map[key]])],
                    }
                )
            # If line is a component that was consumed, then auto deliver
            if sale_line.is_repair_component:
                sale_line.qty_delivered = sale_line.product_uom_qty

            sale_line_map[key] = sale_line

        # Step 6: Create or reuse a single DO for main repaired products
        main_keys = [k for k in sale_line_map.keys() if not k[1]]  # is_component=False
        if main_keys:
            first_key = main_keys[0]
            _, first_repair = move_repair_map[first_key][0]
            picking_type = sale_order.warehouse_id.out_type_id

            # Find existing draft/unassigned picking
            picking = self.env["stock.picking"].search(
                [
                    ("sale_id", "=", sale_order.id),
                    ("picking_type_id", "=", picking_type.id),
                    ("state", "in", ["draft", "waiting"]),
                ],
                limit=1,
            )
            if not picking:
                picking = StockPicking.create(
                    {
                        "picking_type_id": picking_type.id,
                        "partner_id": sale_order.partner_id.id,
                        "origin": sale_order.name,
                        "location_id": first_repair.location_id.id,
                        "location_dest_id": sale_order.partner_id.property_stock_customer.id,
                        "sale_id": sale_order.id,
                        "company_id": sale_order.company_id.id,
                    }
                )

            # Step 7: Create moves & move lines per repair, reusing existing moves
            for key in main_keys:
                line = sale_line_map[key]

                # Check for existing move
                existing_move = picking.move_ids.filtered(
                    lambda m: m.sale_line_id == line
                )
                if existing_move:
                    move = existing_move
                    # Update qty
                    existing_lots = move.move_line_ids.mapped("lot_id").ids
                    new_qty = sum(
                        r.product_qty or 1.0
                        for _, r in move_repair_map[key]
                        if r.lot_id.id not in existing_lots
                    )
                    if new_qty:
                        move.product_uom_qty += new_qty
                else:
                    move_vals = {
                        "name": line.name,
                        "product_id": line.product_id.id,
                        "product_uom_qty": sum(
                            r.product_qty or 1.0 for _, r in move_repair_map[key]
                        ),
                        "product_uom": line.product_uom.id,
                        "location_id": first_repair.location_id.id,
                        "location_dest_id": sale_order.partner_id.property_stock_customer.id,
                        "picking_id": picking.id,
                        "sale_line_id": line.id,
                        "restrict_partner_id": repair.partner_id.id,
                        "company_id": sale_order.company_id.id,
                    }
                    move = StockMove.create(move_vals)

                # Create move lines per repair if not existing
                existing_lots = move.move_line_ids.mapped("lot_id").ids
                for _, repair in move_repair_map[key]:
                    if repair.lot_id and repair.lot_id.id not in existing_lots:
                        self.env["stock.move.line"].create(
                            {
                                "move_id": move.id,
                                "product_id": move.product_id.id,
                                "qty_done": repair.product_qty or 1.0,
                                "product_uom_id": move.product_uom.id,
                                "location_id": repair.location_id.id,
                                "location_dest_id": sale_order.partner_id.property_stock_customer.id,
                                "lot_id": repair.lot_id.id,
                                "company_id": move.company_id.id,
                            }
                        )
            # Confirm & assign picking
            picking.action_confirm()
            picking.action_assign()
            picking.sale_id = sale_order
            picking.owner_id = repair.partner_id

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
