from odoo import api, fields, models
from odoo.exceptions import UserError


class HelpdeskTicketImportSale(models.TransientModel):
    _name = "helpdesk.ticket.import.sale"
    _description = "Import Sale Order for Repairs"

    ticket_id = fields.Many2one(
        "helpdesk.ticket", string="Helpdesk Ticket", required=True
    )
    sale_order_id = fields.Many2one("sale.order", string="Sale Order", required=True)
    line_ids = fields.One2many(
        "helpdesk.ticket.import.sale.line", "wizard_id", string="Sale Order Lines"
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
        """Create repair.batch records based on selected lines."""
        if not self.line_ids:
            raise UserError("No sale order lines selected.")

        repair_batch_model = self.env["repair.batch"]
        for line in self.line_ids:
            if line.qty <= 0:
                raise UserError(f"Invalid quantity for product {line.product_id.name}.")

            # Check if a repair batch already exists for the same product and ticket
            existing_batch = repair_batch_model.search(
                [
                    ("ticket_id", "=", self.ticket_id.id),
                    ("product_id", "=", line.product_id.id),
                    ("qty", "=", line.qty),
                ],
                limit=1,
            )

            if existing_batch:
                continue  # Avoid creating duplicate batches

            repair_batch_model.create(
                {
                    "ticket_id": self.ticket_id.id,
                    "product_id": line.product_id.id,
                    "qty": line.qty,
                    "lot_ids": [(6, 0, line.lot_ids.ids)],  # Add lots to repair batch
                }
            )
        return {"type": "ir.actions.act_window_close"}


class HelpdeskTicketImportSaleLine(models.TransientModel):
    _name = "helpdesk.ticket.import.sale.line"
    _description = "Sale Order Line for Repair Import"

    wizard_id = fields.Many2one("helpdesk.ticket.import.sale", required=True)
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale Order Line")
    product_id = fields.Many2one("product.product", string="Product", required=True)
    qty = fields.Float(string="Quantity", default=1.0)
    lot_ids = fields.Many2many(
        "stock.lot",
        string="Serial Numbers",
    )
