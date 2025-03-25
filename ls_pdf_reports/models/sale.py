# Import Odoo libs
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def get_quote_report_data(self):
        """Get the Sale Order related report data"""

        data = {}
        for order in self:
            order_data = order.get_report_data()
            data[order.id] = order_data
        return data

    def get_report_data(self):
        """Collect order information into a dict, that can be used in reports"""

        self.ensure_one()

        order_data = {
            'product_lines': [],
        }

        product_lines = self.order_line.filtered(lambda l: not l.is_delivery)

        for sale_order_line in product_lines:

            # TODO: "sale_order_line.quote_config_id" Field not found
            quote_config = sorted_quote_lines = False
            # quote_config = sale_order_line.quote_config_id or False
            #
            # if quote_config:
            #     quote_lines = quote_config.quote_config_line_ids.filtered(
            #         lambda l: l.description_type != 'hide'
            #     )
            #     sorted_quote_lines = quote_lines.sorted(key=lambda q: q.sequence)
            #     # self.print_quote_data_for_debug(quote_config, sorted_quote_lines)
            # else:
            #     sorted_quote_lines = False

            order_line_data = {
                'order_line': sale_order_line,
                'quote_config': quote_config,
                'quote_lines': sorted_quote_lines,
            }

            order_data['product_lines'].append(order_line_data)

        # Set the shipping lines
        shipping_lines = self.order_line.filtered(lambda l: l.is_delivery)

        order_data['shipping_lines'] = shipping_lines
        order_data['product_subtotal_amount'] = sum(product_lines.mapped('price_subtotal'))
        order_data['shipping_subtotal_amount'] = sum(shipping_lines.mapped('price_subtotal'))

        return order_data


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_line_serial_numbers(self):
        """
        Get a list of serial numbers for this sale line
        """
        self.ensure_one()

        return self.move_ids.move_line_ids.mapped('lot_id.name')
