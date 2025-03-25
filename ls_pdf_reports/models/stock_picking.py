# Import Python Libs
import uuid

# Import Odoo libs
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def get_shipping_value(self):
        """
        Get the price of all the related sale lines
        """
        self.ensure_one()
        return sum(self.mapped('move_ids.origin_sale_line_ids.price_subtotal'))

    def get_packing_product_lines(self):
        """Collect the data for the Packing/Picking product lines"""

        self.ensure_one()

        product_lines = []

        # Order the lines by the location row
        moves = self.move_ids.sorted(key=lambda m: m.product_id.product_tmpl_id.loc_row or '')

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

            # Get the product line where these attribute match with the current move:
            #   - sale_order_line
            #   - manufacturing order
            #   - product
            #   - origin moves location
            similar_product_line = next(
                iter(
                    filter(
                        lambda l: l.get('production_id') == move.origin_production_id.id
                        and l.get('product_id') == product.id
                        and l.get('stock_move').location_dest_id.name == move.location_dest_id.name
                        or l.get('origin_sale_line_id') == sale_order_line.id,
                        product_lines,
                    )
                ),
                None,
            )

            if similar_product_line:
                # If a similar product_line already exists
                # don't create a new product_line for it

                if (
                    similar_product_line.get('sale_line', False) != sale_order_line
                    and qty_adjusted_sale_order_lines.get(sale_order_line.id, False) != similar_product_line.get('uuid', None)
                ): 
                    # If the similar product_line is not for the current Sale Order Line
                    # and the current Sale Order Line was not already used to adjust this similar product_line's qty
                    # increase the similar product_line's qty by the current qty
                    similar_product_line['qty'] += qty
                    # Keep track of Sale Order Lines that we used to adjust an existing product_line's qty
                    qty_adjusted_sale_order_lines[sale_order_line.id] = similar_product_line.get('uuid')
                continue

            lot_ids = self.get_serials_for_product(product_id=move_product)
            serials = lot_ids.mapped('name') if lot_ids else False

            # Assemble the product dict
            product_line_data = {
                # Generate a unique identifier for this product line
                'uuid': str(uuid.uuid4()),
                'production_id': move.origin_production_id.id or False,
                'product_id': product.id,
                'product_default_code': product.product_tmpl_id.default_code,
                'product_name': product.name,
                'product_tmpl': product.product_tmpl_id,
                'origin_sale_line_id': sale_order_line.id,
                'qty': qty,
                'stock_move': move,
                'sale_line': sale_order_line or False,
                'system_serial_numbers': serials,
            }

            product_lines.append(product_line_data)
        return product_lines

    def get_picking_product_lines(self):
        """Collect the data for the Packing/Picking product lines"""

        self.ensure_one()

        product_lines = []

        # Order the lines by the location row
        # TODO: Update this to also sort by rack / shelfs
        moves = self.move_ids.sorted(
            key=lambda m: int(m.product_id.product_tmpl_id.loc_row.split()[0])
            if m.product_id.product_tmpl_id.loc_row
            else 0
        )

        for move in moves:

            # Get the product line where these attribute match with the current move:
            #   - manufacturing order
            #   - product
            #   - origin moves location
            similar_product_line = next(
                iter(
                    filter(
                        lambda l: l.get('production_id') == move.origin_production_id.id
                        and l.get('product_id') == move.product_id.id
                        and l.get('stock_move').location_dest_id.name == move.location_dest_id.name,
                        product_lines,
                    )
                ),
                None,
            )

            lot_ids = self.get_serials_for_product(product_id=move.product_id)
            serials = lot_ids.mapped('name') if lot_ids else False

            if similar_product_line:
                # If there is a similar line we only want to raise the qty
                qty = similar_product_line.get('qty') + move.product_uom_qty
                similar_product_line.update({'qty': qty})
            else:
                # If there is no similar line we want to create a new one
                product_line_data = {
                    'production_id': move.origin_production_id.id or False,
                    'product_id': move.product_id.id,
                    'product_default_code': move.product_id.product_tmpl_id.default_code,
                    'product_name': move.product_id.name,
                    'product_tmpl': move.product_id.product_tmpl_id,
                    'qty': move.product_uom_qty,
                    'stock_move': move,
                    'sale_line': move.sale_line_id or False,
                    'system_serial_numbers': serials,
                }

                product_lines.append(product_line_data)

        return product_lines
