from odoo import api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicketImportSale(models.TransientModel):
    _name = "helpdesk.ticket.import.sale"
    _description = "Import Sale Order for Repairs"

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

    @api.onchange("sale_order_id")
    def _onchange_sale_order(self):
        if self.sale_order_id:
            lines = []
            for line in self.sale_order_id.order_line:
                # Fetch serial numbers (lots) for this specific product in the sale order
                lot_ids = self.env["stock.lot"].search(
                    [("product_id", "=", line.product_id.id)]
                )

                # Manually filter the lots by checking their sale_order_ids computed field
                filtered_lots = lot_ids.filtered(
                    lambda lot: self.sale_order_id.id in lot.sale_order_ids.ids
                )

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
            repair_batch_model.create(
                {
                    "ticket_id": self.ticket_id.id,
                    "partner_id": self.partner_id.id,
                    "product_id": product_id,
                    "qty": data["qty"],
                    "lot_ids": [(6, 0, list(data["lot_ids"]))],  # Convert set to list
                }
            )

        # Assign partner if not already set
        if not self.ticket_id.partner_id:
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
