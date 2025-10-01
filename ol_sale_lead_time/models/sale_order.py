# Import Odoo libs
from datetime import timedelta
from odoo import api, models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    first_estimated_ship_date = fields.Date(
        string="First Estimated Ship Date",
        readonly=True,
        copy=False,
    )

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order.action_compute_esd()
            if not order.first_estimated_ship_date and order.expected_date:
                order.first_estimated_ship_date = order.expected_date.date()
        return res

    @api.depends("order_line.customer_lead", "date_order", "state")
    def _compute_expected_date(self):
        super()._compute_expected_date()
        for order in self:
            if order.expected_date:
                weekday = order.expected_date.weekday()
                if weekday == 5:
                    order.expected_date += timedelta(days=2)
                elif weekday == 6:
                    order.expected_date += timedelta(days=1)

    def action_compute_esd(self):
        for order in self:
            order.order_line._compute_customer_lead()
