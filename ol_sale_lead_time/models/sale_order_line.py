# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import timedelta


class SaleOrderLine(models.Model):
    """Extend sale order line with ESD calculation fields."""
    _inherit = 'sale.order.line'

    customer_lead = fields.Integer(
        string='Customer Lead (days)',
        default=0,
        help='Lead time in days for this line'
    )

    available_date = fields.Date(
        string='Available Date',
        compute='_compute_available_date',
        store=True,
        help='Date when this line can ship (today + customer_lead)'
    )

    bottleneck_component_id = fields.Many2one(
        'product.product',
        string='Bottleneck Component',
        readonly=True,
        help='Component causing longest lead time for this line'
    )

    @api.depends('customer_lead')
    def _compute_available_date(self):
        """Calculate available date based on customer lead time."""
        today = fields.Date.today()
        for line in self:
            if line.customer_lead:
                line.available_date = today + timedelta(days=line.customer_lead)
            else:
                line.available_date = False
