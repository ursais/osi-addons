# Import libs
from collections import Counter

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
        string="Related Sale Orders",
    )
    out_transfer_count = fields.Integer(
        string="OUT Count",
        compute="_compute_transfer_counts",
    )
    out_transfer_count = fields.Integer(
        string="OUT Count",
        compute="_compute_transfer_counts",
    )
    in_transfer_count = fields.Integer(
        string="IN Count",
        compute="_compute_transfer_counts",
    )
    show_generate_repairs = fields.Boolean(
        string="Show Generate Repairs Button",
        compute="_compute_show_generate_repairs",
    )

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

    def _compute_transfer_counts(self):
        for ticket in self:
            ticket.out_transfer_count = len(
                ticket.repair_sale_order_ids.mapped("picking_ids")
            )
            ticket.in_transfer_count = len(
                self.env["stock.picking"].search([("ticket_id", "=", self.id)])
            )

    def action_view_out_transfers(self):
        """View outbound transfers related to sale order deliveries."""
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        transfers = self.repair_sale_order_ids.mapped("picking_ids")

        if len(transfers) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": transfers.id,
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", transfers.ids)],
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

    def action_view_in_transfers(self):
        """View inbound transfers (receipts) related to this ticket."""
        action = self.env.ref("stock.action_picking_tree_all").read()[0]
        transfers = self.env["stock.picking"].search([("ticket_id", "=", self.id)])

        if len(transfers) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "res_id": transfers.id,
                }
            )
        else:
            action.update(
                {
                    "domain": [("id", "in", transfers.ids)],
                }
            )

        return action

    def action_create_receipt(self):
        stock_picking_obj = self.env["stock.picking"]
        stock_move_obj = self.env["stock.move"]
        stock_move_line_obj = self.env["stock.move.line"]

        if not self.repair_batch_ids:
            raise ValueError("No repair batches linked to this ticket.")

        product_quantities = {}  # {product_id: {"qty": total_qty, "lots": []}}
        locations = {"source": [], "destination": []}

        for batch in self.repair_batch_ids:
            for repair in batch.repair_ids.filtered(
                lambda r: r.state not in ("done", "under_repair", "cancel")
            ):
                if repair.location_id:
                    locations["source"].append(repair.location_id.id)
                if repair.location_dest_id:
                    locations["destination"].append(repair.location_dest_id.id)

                product_id = repair.product_id.id
                lot_id = (
                    repair.lot_id.id if repair.lot_id else False
                )  # ✅ Use lot_id from repair

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
                                "qty_done": repair.product_qty,  # ✅ Match quantity with repair qty
                            },
                        )
                    )

        if not product_quantities:
            raise ValueError("No valid products found to create a receipt.")

        # Determine the most common source & destination location (fallback to first if multiple)
        source_location_id = (
            Counter(locations["source"]).most_common(1)[0][0]
            if locations["source"]
            else False
        )
        destination_location_id = (
            Counter(locations["destination"]).most_common(1)[0][0]
            if locations["destination"]
            else False
        )

        if not source_location_id or not destination_location_id:
            raise ValueError(
                "Could not determine valid source and destination locations."
            )

        picking_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "incoming"),
                ("warehouse_id.company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

        if not picking_type:
            raise ValueError("No incoming transfer type found for the company.")

        receipt = stock_picking_obj.create(
            {
                "partner_id": self.partner_id.id,
                "origin": self.name,
                "picking_type_id": picking_type.id,
                "location_id": source_location_id,
                "location_dest_id": destination_location_id,
                "ticket_id": self.id,
            }
        )

        for product_id, data in product_quantities.items():
            product = self.env["product.product"].browse(product_id)
            stock_move = stock_move_obj.create(
                {
                    "picking_id": receipt.id,
                    "product_id": product_id,
                    "name": product.display_name,  # ✅ Set product name as move description
                    "product_uom": product.uom_id.id,
                    "product_uom_qty": data["qty"],
                    "location_id": source_location_id,
                    "location_dest_id": destination_location_id,
                }
            )

            # Create stock move lines with lot tracking
            for lot in data["lots"]:
                lot[2]["move_id"] = stock_move.id
                stock_move_line_obj.create(lot[2])

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
            lambda r: not r.sale_order_id
        )

        if not repair_orders:
            raise ValueError("No repairs qualify for a new sale order.")

        new_sale_orders = []

        for batch in self.repair_batch_ids:
            batch_repairs = batch.repair_ids.filtered(lambda r: not r.sale_order_id)
            if not batch_repairs:
                continue

            product_quantities = {}
            move_repair_map = {}

            for repair in batch_repairs:
                for move in repair.move_ids.filtered(
                    lambda m: m.repair_line_type == "add"
                ):
                    product_id = move.product_id.id
                    product_quantities[product_id] = (
                        product_quantities.get(product_id, 0) + move.product_uom_qty
                    )
                    move_repair_map.setdefault(product_id, []).append((move, repair))

            if not product_quantities:
                continue  # Skip if no valid moves for this batch

            sale_order = sale_order_obj.create(
                {
                    "partner_id": self.partner_id.id,
                    "origin": self.name,
                }
            )
            new_sale_orders.append(sale_order.id)

            product_sale_lines = {}

            for product_id, qty in product_quantities.items():
                product = self.env["product.product"].browse(product_id)
                sale_line = sale_order_line_obj.create(
                    {
                        "order_id": sale_order.id,
                        "product_id": product_id,
                        "product_uom_qty": qty,
                        "product_uom": product.uom_id.id,
                        "price_unit": product.list_price,
                    }
                )
                product_sale_lines[product_id] = sale_line.id

            # Link repair orders and moves to the created sale order and sale lines
            for product_id, move_repairs in move_repair_map.items():
                sale_line_id = product_sale_lines.get(product_id)
                for move, repair in move_repairs:
                    repair.sale_order_id = sale_order.id
                    repair.sale_order_line_id = sale_line_id

        if not new_sale_orders:
            raise ValueError("No valid products found to create a sale order.")

        self.repair_sale_order_ids = [(6, 0, new_sale_orders)]  # Assign multiple SOs

        return {
            "name": "Sale Orders",
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "tree,form",
            "domain": [("id", "in", new_sale_orders)],
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
