# Import Python Libs
import uuid

# Import Odoo libs
from odoo import api, fields, models


class StockPicking(models.Model):
    """Inherit stock Picking to unreserve on creation if operation type is set to."""

    _inherit = "stock.picking"

    # COLUMNS #####

    can_add_stock_moves = fields.Boolean(
        string="Can Add Stock Moves",
        compute="_compute_can_add_stock_moves",
    )
    company_currency_id = fields.Many2one(related="company_id.currency_id")
    total_sales_price = fields.Monetary(
        string="Total Sales Price",
        compute="_compute_total_sales_price",
        currency_field="company_currency_id",
        store=True,
        help="The total of the sales price (from sale order or product sales price) of all done products and the shipping cost",
    )

    # END #########
    # METHODS #####

    @api.depends(
        "state",
        "move_ids.sale_line_id.qty_delivered",
        "move_ids.sale_line_id.product_uom_qty",
    )
    def _compute_total_sales_price(self):
        """Compute the total sales price for the picking, including delivery costs."""
        for picking in self:
            # Calculate the total carrier price from delivery sale lines
            carrier_price = sum(
                picking.sale_id.mapped("order_line")
                .filtered(lambda sol: sol.is_delivery)
                .mapped("price_unit")
            )

            # Calculate the total amount from each sale line based on delivered quantity
            sale_line_amount = sum(
                sale_line.price_unit * sale_line.product_uom_qty
                for sale_line in picking.mapped("move_ids.sale_line_id")
            )

            # Update the total sales price with the sum of sale line amounts and carrier price
            picking.total_sales_price = sale_line_amount + carrier_price

    def _compute_can_add_stock_moves(self):
        for rec in self:
            # For receipts only allow adding a line if the user has the security group
            is_receipt = rec.picking_type_id and rec.picking_type_id.code == "incoming"
            if is_receipt:
                rec.can_add_stock_moves = self.env.user.has_group(
                    "ol_stock.group_allow_incoming_move_addition"
                )
            else:
                # For all other transfers, let users add a line
                rec.can_add_stock_moves = True

    def action_confirm(self):
        # Call the original button_validate method to confirm the picking
        res = super().action_confirm()

        # After the picking is confirmed, check if unreserve_on_create is enabled
        for picking in self:
            if (
                picking.picking_type_id.code == "incoming"
                and picking.picking_type_id.unreserve_on_create
            ):
                # Unreserve stock moves for incoming shipments
                picking.do_unreserve()

        return res

    def get_shipping_value(self):
        """
        Get the price of all the related sale lines
        """
        self.ensure_one()
        return sum(self.mapped("move_ids.sale_line_id.price_subtotal"))

    def get_packing_product_lines(self):
        """Collect the data for the Packing/Picking product lines"""

        self.ensure_one()

        product_lines = []

        # Order the lines by the location row
        moves = self.move_ids.sorted(key=lambda m: m.location_id and m.location_id.id)

        # Keep track of Sale Order Line's for which an existing product_line's qty was already increased
        qty_adjusted_sale_order_lines = {}

        for move in moves:
            # Product on the related sale order line
            sale_order_line = move.sale_line_id
            sale_order_line_product = sale_order_line.product_id
            move_product = move.product_id

            # This move could be a result of a CSV Import
            # in which case there is no Sale Order Line
            # which we would like to use as a default
            product = sale_order_line_product or move_product
            qty = sale_order_line and sale_order_line.product_qty or move.product_qty
            lot_ids = move.lot_ids
            # Get the product line where these attribute match with the current move:
            #   - sale_order_line
            #   - manufacturing order
            #   - product
            #   - origin moves location
            similar_product_line = next(
                iter(
                    filter(
                        lambda l: l.get("product_id") == product.id
                        and l.get("stock_move").location_dest_id.name
                        == move.location_dest_id.name
                        or l.get("origin_sale_line_id") == sale_order_line.id,
                        product_lines,
                    )
                ),
                None,
            )
            if similar_product_line:
                # If a similar product_line already exists
                # don't create a new product_line for it

                if similar_product_line.get(
                    "sale_line", False
                ) != sale_order_line and qty_adjusted_sale_order_lines.get(
                    sale_order_line.id, False
                ) != similar_product_line.get(
                    "uuid", None
                ):
                    # If the similar product_line is not for the current Sale Order Line
                    # and the current Sale Order Line was not already used to adjust this similar product_line's qty
                    # increase the similar product_line's qty by the current qty
                    similar_product_line["qty"] += qty
                    # Keep track of Sale Order Lines that we used to adjust an existing product_line's qty
                    qty_adjusted_sale_order_lines[sale_order_line.id] = (
                        similar_product_line.get("uuid")
                    )
                if move.product_id.tracking == 'serial':
                    system_serial_numbers = similar_product_line["system_serial_numbers"]
                    system_serial_numbers.extend(lot_ids.mapped("name"))
                    similar_product_line["system_serial_numbers"] = system_serial_numbers
                continue
            serials = move.lot_ids.mapped("name") if move.lot_ids else False

            # Assemble the product dict
            product_line_data = {
                # Generate a unique identifier for this product line
                "uuid": str(uuid.uuid4()),
                "production_id": move.production_id.id or False,
                "production_id": False,
                "product_id": product.id,
                "product_default_code": product.product_tmpl_id.default_code,
                "product_name": product.name,
                "product_tmpl": product.product_tmpl_id,
                "origin_sale_line_id": sale_order_line.id,
                "qty": qty,
                "stock_move": move,
                "sale_line": sale_order_line or False,
                "system_serial_numbers": serials,
            }

            product_lines.append(product_line_data)

        return product_lines

    def get_picking_product_lines(self):
        """Collect the data for the Packing/Picking product lines"""

        self.ensure_one()

        product_lines = []

        moves = self.move_ids.sorted(key=lambda m: m.location_id and m.location_id.id)

        for move in moves:
            # Get the product line where these attribute match with the current move:
            #   - manufacturing order
            #   - product
            #   - origin moves location
            similar_product_line = next(
                iter(
                    filter(
                        lambda l: l.get("product_id") == move.product_id.id
                        and l.get("stock_move").location_dest_id.name
                        == move.location_dest_id.name,
                        product_lines,
                    )
                ),
                None,
            )

            serials = move.lot_ids.mapped("name") if move.lot_ids else False

            if similar_product_line:
                # If there is a similar line we only want to raise the qty
                qty = similar_product_line.get("qty") + move.product_uom_qty
                similar_product_line.update({"qty": qty})
            else:
                # If there is no similar line we want to create a new one
                product_line_data = {
                    "production_id": move.production_id.id or False,
                    "production_id": False,
                    "product_id": move.product_id.id,
                    "product_default_code": move.product_id.product_tmpl_id.default_code,
                    "product_name": move.product_id.name,
                    "product_tmpl": move.product_id.product_tmpl_id,
                    "qty": move.product_uom_qty,
                    "stock_move": move,
                    "sale_line": move.sale_line_id or False,
                    "system_serial_numbers": serials,
                }

                product_lines.append(product_line_data)
        return product_lines

    def get_picking_move_lines(self):
        """Collect the data for the Packing/Picking product lines"""

        self.ensure_one()

        product_lines = []

        moves = self.move_ids.sorted(key=lambda m: m.location_id and m.location_id.id)

        for move in moves:
            for line in move.move_line_ids:
                serial = line.lot_id.name if line.lot_id else False
                product_line_data = {
                    "location_id": line.location_id.name,
                    "product_default_code": line.product_id.product_tmpl_id.default_code,
                    "qty": line.quantity,
                    "product_name": line.product_id.name,
                    "system_serial_numbers": serial,
                    "location_dest_id": line.location_dest_id.name,
                }

                product_lines.append(product_line_data)
        return product_lines

    def write(self, vals):
        res = super().write(vals)
        for picking in self:
            # If the picking is an incoming (receipt) and scheduled_date is updated
            if picking.picking_type_code == "incoming" and vals.get("scheduled_date"):
                # Update date on all stock moves to match the new scheduled_date
                picking.move_ids.write({"date": vals.get("scheduled_date")})
        return res

    def _set_scheduled_date(self):
        # Exclude incoming pickings from the default scheduled date setting logic
        records = self.filtered(lambda l: l.picking_type_code != "incoming")

        # Call the parent method only for non-incoming pickings
        return super(StockPicking, records)._set_scheduled_date()

    @api.depends(
        "move_ids.state",
        "move_ids.date",
        "move_type",
    )
    def _compute_scheduled_date(self):
        # Exclude incoming pickings from the default computation of scheduled_date
        records = self.filtered(lambda l: l.picking_type_code != "incoming")

        # Call the parent method only for non-incoming pickings
        return super(StockPicking, records)._compute_scheduled_date()

    # END #########
