# Import Python Libs

# Import Odoo libs
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_invoice_print(self):
        """
        Override original invoice template
        """
        self.ensure_one()
        self.is_move_sent = True
        return self.env.ref('ls_pdf_reports.action_generic_invoice_report').report_action(self)

    def get_report_invoice_data(self):
        data = {}
        for invoice in self:
            data[invoice.id] = {}
            order_data = False

            if invoice.line_ids.sale_line_ids:
                order_data = invoice.get_invoice_report_data_by_sale_order_lines()

            data[invoice.id]['sale_order'] = order_data

        return data

    def get_invoice_report_data_by_sale_order_lines(self):

        order_data = {
            'product_lines': [],
        }

        product_lines = self.env['sale.order.line']

        for invoice_line in self.invoice_line_ids:
            for sale_order_line in invoice_line.sale_line_ids:

                if sale_order_line.is_delivery:
                    continue

                product_lines |= sale_order_line

                # TODO: "sale_order_line.quote_config_id" Field not found
                quote_config = sorted_quote_lines = False
                # quote_config = sale_order_line.quote_config_id or False
                #
                # if quote_config:
                #     quote_lines = quote_config.quote_config_line_ids.filtered(
                #         lambda l: l.description_type != 'hide'
                #     )
                #     sorted_quote_lines = quote_lines.sorted(key=lambda q: q.product_id.sequence)
                # else:
                #     sorted_quote_lines = False

                order_line_data = {
                    'invoice_line': invoice_line,
                    'order_line': sale_order_line,
                    'quote_config': quote_config,
                    'quote_lines': sorted_quote_lines,
                }

                order_data['product_lines'].append(order_line_data)

        # Set the shipping lines
        shipping_lines = self.mapped('invoice_line_ids.sale_line_ids').filtered(lambda l: l.is_delivery)

        order_data['shipping_lines'] = shipping_lines
        order_data['product_subtotal_amount'] = sum(product_lines.mapped('price_subtotal'))
        order_data['shipping_subtotal_amount'] = sum(shipping_lines.mapped('price_subtotal'))

        return order_data

    def get_invoice_report_data(self):

        for invoice in self:

            filtered_invoice = invoice
            filtered_invoice_data = {
                'sum_amount': invoice.amount_total,
                'out_invoice_amount': None,
                'out_refund_amount': None,
                'payment_received_amount': (invoice.amount_total - invoice.amount_residual),
                'residual_amount': invoice.amount_residual,
                'type': invoice.get_report_title(),
            }

        res = {'invoice': filtered_invoice, 'invoice_data': filtered_invoice_data}

        return res

    def get_report_title(self):
        """Return the report title defined by marketing"""

        if self.move_type == 'out_refund':
            return 'Refund'

        return 'Invoice'
