from odoo import models, api, fields, _
from odoo.tools import frozendict

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'



    def _prepare_down_payment_lines_values(self, order):
        """ Modify the original method to remove tax based down payment lines values
        this means we always create only one DownPayment SO Line.
        """
        self.ensure_one()

        if self.advance_payment_method == 'percentage':
            percentage = self.amount / 100
        else:
            percentage = self.fixed_amount / order.amount_total if order.amount_total else 1

        # Remove SO Lines that aare already linked with previous DownPayment Lines, and DP lines too.
        base_downpayment_lines_values = self._prepare_base_downpayment_line_values(order)

        order_lines = order.order_line.filtered(lambda sol: not sol.display_type and not sol.is_downpayment)

        # We are skiping The tax calculation for the order_lines and splitting DP lines by Tax
        # We are also ignoring any tax present on the DP Product itself, maybe revisit this if needed.
        # This ensures the amount in DP is correctly reflected from the SO Lines for which DP is created.
        # Using price_total which includes price+tax-disc
        order_amount_incl_tax = 0.0
        for order_line in order_lines:
            # The Delivery Product somehow has taxed amount in its price_total even when there is no tax applied.
            if order_line.is_delivery and not order_line.tax_id:
                order_amount_incl_tax += order_line.price_subtotal
            else:
                order_amount_incl_tax += order_line.price_total
        # order_amount_incl_tax = sum(order_lines.mapped('price_total'))


        analytic_distribution_order_lines = {}
        for sol in order_lines.filtered(lambda ol: ol.analytic_distribution):
            analytic_distribution_order_lines.update(sol.analytic_distribution)
        base_downpayment_lines_values.update({
            'price_unit': order.currency_id.round(order_amount_incl_tax * percentage),
            'product_uom_qty': 0.0,
            'discount': 0.0,
            'analytic_distribution': analytic_distribution_order_lines,
        })

        # We skip the logic to split the lines based on taxes present on SO lines.

        return [base_downpayment_lines_values]
