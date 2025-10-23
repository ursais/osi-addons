# Import Python libs
from datetime import timedelta

# Import Odoo libs
from odoo import api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicketImportSale(models.TransientModel):
    """Wizard to import products from sale orders to repair batch."""

    _name = "helpdesk.ticket.import.sale"
    _description = "Import Sale Order for Repairs"

    # COLUMNS ###

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Helpdesk Ticket",
        required=True,
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="helpdesk.ticket.import.sale.line",
        inverse_name="wizard_id",
        string="Sale Order Lines",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer",
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Serial Number",
        help="If set, automatically finds the last sale order that delivered this serial.",
    )
    warned_partner_change = fields.Boolean(default=False)

    # END #######
    # METHODS ###

    @api.onchange("lot_id")
    def _onchange_serial_number(self):
        """Auto-find last sale order by serial number."""
        if not self.lot_id:
            return

        MoveLine = self.env["stock.move.line"]
        last_move_line = MoveLine.search(
            [
                ("lot_id", "=", self.lot_id.id),
                ("state", "=", "done"),
                ("move_id.sale_line_id", "!=", False),
                ("location_dest_id.usage", "=", "customer"),
            ],
            order="date desc",
            limit=1,
        )

        if last_move_line:
            self.sale_order_id = last_move_line.move_id.sale_line_id.order_id
        else:
            self.sale_order_id = False
            return {
                "warning": {
                    "title": "No Sale Order Found",
                    "message": f"No delivered sale order found for serial number {self.lot_id.name}.",
                }
            }

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        # --- Check partner change ---
        if (
            self.ticket_id.partner_id
            and self.partner_id != self.ticket_id.partner_id
            and not self.warned_partner_change
        ):
            # Show Warning
            self.warned_partner_change = True

    @api.onchange("sale_order_id")
    def _onchange_sale_order(self):
        if self.sale_order_id:
            # Set Partner
            self.partner_id = self.sale_order_id.partner_id

            lines = []
            for line in self.sale_order_id.order_line:
                # Skip service products
                if line.product_id.type == "service" or line.product_uom_qty <= 0:
                    continue

                # Fetch serial numbers (lots) for this specific product in the sale order
                lot_ids = self.env["stock.lot"].search(
                    [("product_id", "=", line.product_id.id)]
                )

                # Manually filter the lots by checking their sale_order_ids computed field
                filtered_lots = lot_ids.filtered(
                    lambda lot: self.sale_order_id.id in lot.sale_order_ids.ids
                )

                if self.lot_id not in filtered_lots:
                    self.lot_id = False

                lines.append(
                    (
                        0,
                        0,
                        {
                            "sale_order_line_id": line.id,
                            "product_id": line.product_id.id,
                            "qty": line.product_uom_qty,
                            "lot_ids": [(6, 0, filtered_lots.ids)],
                        },
                    )
                )

            self.line_ids = lines

    def action_confirm(self):
        """Create a single repair batch per product, summing quantities and merging lot_ids."""
        if not self.line_ids:
            raise UserError("No sale order lines selected.")

        repair_batch_model = self.env["repair.batch"]
        repair_batches = {}

        for line in self.line_ids:
            if line.qty <= 0:
                raise UserError(f"Invalid quantity for product {line.product_id.name}.")

            product_id = line.product_id.id
            lot_ids = set(line.lot_ids.ids)  # Use a set to merge unique lot IDs

            if product_id in repair_batches:
                repair_batches[product_id]["qty"] += line.qty
                repair_batches[product_id]["lot_ids"].update(lot_ids)
            else:
                repair_batches[product_id] = {
                    "qty": line.qty,
                    "lot_ids": lot_ids,
                }

        # Create repair batches
        for product_id, data in repair_batches.items():
            # Determine if there's a single sale order line for this product
            sale_lines = self.line_ids.filtered(lambda l: l.product_id.id == product_id)
            sale_line_id = (
                sale_lines.sale_order_line_id.id if len(sale_lines) == 1 else False
            )

            batch = repair_batch_model.create(
                {
                    "ticket_id": self.ticket_id.id,
                    "partner_id": self.partner_id.id,
                    "product_id": product_id,
                    "qty": data["qty"],
                    "sale_id": self.sale_order_id.id,
                    "sale_line_id": sale_line_id,
                    "lot_ids": [(6, 0, list(data["lot_ids"]))],
                    "schedule_date": fields.Datetime.now() + timedelta(days=7),
                }
            )
            # Set fields
            batch._onchange_sale_id_set_invoice_date()

        # Assign partner if not already set
        if (
            not self.ticket_id.partner_id
            or self.partner_id != self.ticket_id.partner_id
        ):
            self.ticket_id.partner_id = self.partner_id

        # Append the original sale orders
        if self.sale_order_id:
            self.ticket_id.original_sale_order_ids |= self.sale_order_id

        return {"type": "ir.actions.act_window_close"}


class HelpdeskTicketImportSaleLine(models.TransientModel):
    _name = "helpdesk.ticket.import.sale.line"
    _description = "Sale Order Line for Repair Import"

    wizard_id = fields.Many2one(
        comodel_name="helpdesk.ticket.import.sale",
        required=True,
    )
    sale_order_line_id = fields.Many2one(
        comodel_name="sale.order.line",
        string="Sale Order Line",
    )
    sale_order_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sale Order",
        related="sale_order_line_id.order_id",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        required=True,
    )
    qty = fields.Float(
        string="Quantity",
        default=1.0,
    )
    lot_ids = fields.Many2many(
        comodel_name="stock.lot",
        string="Serial Numbers",
    )

    # END #######
    # METHODS ###

    @api.onchange("lot_ids")
    def _onchange_lot_ids(self):
        for line in self:
            line.qty = len(line.lot_ids)

    # END #######
